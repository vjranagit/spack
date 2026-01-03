# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
"""Parser for spec literals

Here is the EBNF grammar for a spec::

    spec          = [name] [node_options] { ^[edge_properties] node } |
                    [name] [node_options] hash |
                    filename

    node          =  name [node_options] |
                     [name] [node_options] hash |
                     filename

    node_options    = [@(version_list|version_pair)] [%compiler] { variant }
    edge_properties = [ { bool_variant | key_value } ]

    hash          = / id
    filename      = (.|/|[a-zA-Z0-9-_]*/)([a-zA-Z0-9-_./]*)(.json|.yaml)

    name          = id | namespace id
    namespace     = { id . }

    variant       = bool_variant | key_value | propagated_bv | propagated_kv
    bool_variant  =  +id |  ~id |  -id
    propagated_bv = ++id | ~~id | --id
    key_value     =  id=id |  id=quoted_id
    propagated_kv = id==id | id==quoted_id

    compiler      = id [@version_list]

    version_pair  = git_version=vid
    version_list  = (version|version_range) [ { , (version|version_range)} ]
    version_range = vid:vid | vid: | :vid | :
    version       = vid

    git_version   = git.(vid) | git_hash
    git_hash      = [A-Fa-f0-9]{40}

    quoted_id     = " id_with_ws " | ' id_with_ws '
    id_with_ws    = [a-zA-Z0-9_][a-zA-Z_0-9-.\\s]*
    vid           = [a-zA-Z0-9_][a-zA-Z_0-9-.]*
    id            = [a-zA-Z0-9_][a-zA-Z_0-9-]*

Identifiers using the ``<name>=<value>`` command, such as architectures and
compiler flags, require a space before the name.

There is one context-sensitive part: ids in versions may contain ``.``, while
other ids may not.

There is one ambiguity: since ``-`` is allowed in an id, you need to put
whitespace space before ``-variant`` for it to be tokenized properly.  You can
either use whitespace, or you can just use ``~variant`` since it means the same
thing.  Spack uses ``~variant`` in directory names and in the canonical form of
specs to avoid ambiguity.  Both are provided because ``~`` can cause shell
expansion when it is the first character in an id typed on the command line.
"""
import json
import pathlib
import re
import sys
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import spack.config
import spack.deptypes
import spack.error
import spack.version
from spack.aliases import LEGACY_COMPILER_TO_BUILTIN
from spack.enums import PropagationPolicy
from spack.llnl.util.tty import color

if TYPE_CHECKING:
    import spack.spec

#: Valid name for specs and variants. Here we are not using
#: the previous ``w[\w.-]*`` since that would match most
#: characters that can be part of a word in any language
IDENTIFIER = r"(?:[a-zA-Z_0-9][a-zA-Z_0-9\-]*)"
DOTTED_IDENTIFIER = rf"(?:{IDENTIFIER}(?:\.{IDENTIFIER})+)"
GIT_HASH = r"(?:[A-Fa-f0-9]{40})"
#: Git refs include branch names, and can contain ``.`` and ``/``
GIT_REF = r"(?:[a-zA-Z_0-9][a-zA-Z_0-9./\-]*)"
GIT_VERSION_PATTERN = rf"(?:(?:git\.(?:{GIT_REF}))|(?:{GIT_HASH}))"

#: Substitute a package for a virtual, e.g., c,cxx=gcc.
#: NOTE: Overlaps w/KVP; this should be first if matched in sequence.
VIRTUAL_ASSIGNMENT = (
    r"(?:"
    rf"(?P<virtuals>{IDENTIFIER}(?:,{IDENTIFIER})*)"  # comma-separated virtuals
    rf"=(?P<substitute>{DOTTED_IDENTIFIER}|{IDENTIFIER})"  # package to substitute
    r")"
)

STAR = r"\*"

NAME = r"[a-zA-Z_0-9][a-zA-Z_0-9\-.]*"

HASH = r"[a-zA-Z_0-9]+"

#: These are legal values that *can* be parsed bare, without quotes on the command line.
VALUE = r"(?:[a-zA-Z_0-9\-+\*.,:=%^\~\/\\]+)"

#: Quoted values can be *anything* in between quotes, including escaped quotes.
QUOTED_VALUE = r"(?:'(?:[^']|(?<=\\)')*'|\"(?:[^\"]|(?<=\\)\")*\")"

VERSION = r"=?(?:[a-zA-Z0-9_][a-zA-Z_0-9\-\.]*\b)"
VERSION_RANGE = rf"(?:(?:{VERSION})?:(?:{VERSION}(?!\s*=))?)"
VERSION_LIST = rf"(?:{VERSION_RANGE}|{VERSION})(?:\s*,\s*(?:{VERSION_RANGE}|{VERSION}))*"

SPLIT_KVP = re.compile(rf"^({NAME})(:?==?)(.*)$")

#: A filename starts either with a ``.`` or a ``/`` or a ``{name}/``, or on Windows, a drive letter
#: followed by a colon and ``\`` or ``.`` or ``{name}\``
WINDOWS_FILENAME = r"(?:\.|[a-zA-Z0-9-_]*\\|[a-zA-Z]:\\)(?:[a-zA-Z0-9-_\.\\]*)(?:\.json|\.yaml)"
UNIX_FILENAME = r"(?:\.|\/|[a-zA-Z0-9-_]*\/)(?:[a-zA-Z0-9-_\.\/]*)(?:\.json|\.yaml)"
FILENAME = WINDOWS_FILENAME if sys.platform == "win32" else UNIX_FILENAME

#: Regex to strip quotes. Group 2 will be the unquoted string.
STRIP_QUOTES = re.compile(r"^(['\"])(.*)\1$")

#: Values that match this (e.g., variants, flags) can be left unquoted in Spack output
NO_QUOTES_NEEDED = re.compile(r"^[a-zA-Z0-9,/_.\-\[\]]+$")


class SpecTokenizationError(spack.error.SpecSyntaxError):
    """Syntax error in a spec string"""

    def __init__(self, text: str):
        super().__init__(f"unexpected characters in the spec string\n{text}\n")


def parse(text: str) -> List["spack.spec.Spec"]:
    """Parse text into a list of strings

    Args:
        text (str): text to be parsed

    Return:
        List of specs
    """
    return SpecParser(text).all_specs()


def parse_one_or_raise(
    text: str, initial_spec: Optional["spack.spec.Spec"] = None
) -> "spack.spec.Spec":
    """Parse exactly one spec from text and return it, or raise

    Args:
        text (str): text to be parsed
        initial_spec: buffer where to parse the spec. If None a new one will be created.
    """
    parser = SpecParser(text)
    result = parser.next_spec(initial_spec)

    if parser.match:
        message = f"expected a single spec, but got more:\n{text}"
        start = parser.match.start()
        end = parser.match.end()
        # Adjust start to skip leading whitespace in the match
        matched_text = parser.match.group()
        stripped_text = matched_text.lstrip()
        start += len(matched_text) - len(stripped_text)
        underline = f"\n{' ' * start}{'^' * (end - start)}"
        message += color.colorize(f"@*r{{{underline}}}")
        raise ValueError(message)

    if result is None:
        raise ValueError("expected a single spec, but got none")

    return result


class SpecParsingError(spack.error.SpecSyntaxError):
    """Error when parsing tokens"""

    def __init__(self, message, token, text):
        message += f"\n{text}"
        if token:
            underline = f"\n{' '*token.start}{'^'*(token.end - token.start)}"
            message += color.colorize(f"@*r{{{underline}}}")
        super().__init__(message)


def strip_quotes_and_unescape(string: str) -> str:
    """Remove surrounding single or double quotes from string, if present."""
    match = STRIP_QUOTES.match(string)
    if not match:
        return string

    # replace any escaped quotes with bare quotes
    quote, result = match.groups()
    return result.replace(rf"\{quote}", quote)


def quote_if_needed(value: str) -> str:
    """Add quotes around the value if it requires quotes.

    This will add quotes around the value unless it matches :data:`NO_QUOTES_NEEDED`.

    This adds:

    * single quotes by default
    * double quotes around any value that contains single quotes

    If double quotes are used, we json-escape the string. That is, we escape ``\\``,
    ``"``, and control codes.

    """
    if NO_QUOTES_NEEDED.match(value):
        return value

    return json.dumps(value) if "'" in value else f"'{value}'"


class SpecTokens:
    END_EDGE_PROPERTIES = rf"\](?:\s*{VIRTUAL_ASSIGNMENT})?"
    DEPENDENCY = rf"(?:\^|\%\%|\%)(?:(?P<edge_bracket>\[)|(?:\s*{VIRTUAL_ASSIGNMENT})?)"
    VERSION = (
        rf"@(?:(?P<git_version>{GIT_VERSION_PATTERN}(?:={VERSION})?)"
        rf"|\s*(?P<version_list>{VERSION_LIST}))"
    )
    BOOL_VARIANT = rf"(?P<bv_prefix>\+\+|~~|--|[~+-])\s*(?P<bv_name>{NAME})"
    KEY_VALUE_PAIR = rf"(?P<kv_name>{NAME})(?P<kv_sep>:?==?)(?P<kv_value>{VALUE}|{QUOTED_VALUE})"
    FILENAME = FILENAME
    FULLY_QUALIFIED_PACKAGE_NAME = DOTTED_IDENTIFIER
    UNQUALIFIED_PACKAGE_NAME = rf"(?:{IDENTIFIER}|{STAR})"
    DAG_HASH = rf"/(?P<dag_hash>{HASH})"
    UNEXPECTED = r"."


RAW_PATTERNS = [
    ("END_EDGE_PROPERTIES", SpecTokens.END_EDGE_PROPERTIES),
    ("DEPENDENCY", SpecTokens.DEPENDENCY),
    ("VERSION", SpecTokens.VERSION),
    ("BOOL_VARIANT", SpecTokens.BOOL_VARIANT),
    ("KEY_VALUE_PAIR", SpecTokens.KEY_VALUE_PAIR),
    ("FILENAME", SpecTokens.FILENAME),
    ("FULLY_QUALIFIED_PACKAGE_NAME", SpecTokens.FULLY_QUALIFIED_PACKAGE_NAME),
    ("UNQUALIFIED_PACKAGE_NAME", SpecTokens.UNQUALIFIED_PACKAGE_NAME),
    ("DAG_HASH", SpecTokens.DAG_HASH),
    ("UNEXPECTED", SpecTokens.UNEXPECTED),
]

_regex_parts = []
for _name, _pattern in RAW_PATTERNS:
    # Rename groups: (?P<groupname> -> (?P<TOKENNAME_groupname>
    _renamed_pattern = re.sub(r"\(\?P<([a-zA-Z_0-9]+)>", f"(?P<{_name}_\\1>", _pattern)
    _regex_parts.append(f"(?P<{_name}>{_renamed_pattern})")

# Global regex that skips whitespace before matching any token
FAST_SPEC_REGEX = re.compile(r"\s*(?:" + "|".join(_regex_parts) + r")")


class SpecParser:
    """Fast spec parser using a single compiled regex"""

    __slots__ = "literal_str", "scanner", "match", "toolchains", "parsed_toolchains"

    def __init__(self, literal_str: str):
        self.literal_str = literal_str.rstrip()
        self.scanner = FAST_SPEC_REGEX.scanner(self.literal_str)  # type: ignore[attr-defined]
        self.match = self.scanner.match()

        # TODO: Move toolchains out of the parser, and expand them as a separate step
        self.toolchains = {}
        configuration = getattr(spack.config, "CONFIG", None)
        if configuration is not None:
            self.toolchains = configuration.get_config("toolchains")
        self.parsed_toolchains: Dict[str, "spack.spec.Spec"] = {}

    def tokens(self, with_subgroups: bool = False) -> List[Tuple[str, str, Dict[str, str]]]:
        """Tokenize the spec string into a list of (kind, match, subgroups) tuples."""
        tokens: List[Tuple[str, str, Dict[str, str]]] = []
        scanner = FAST_SPEC_REGEX.scanner(self.literal_str)  # type: ignore[attr-defined]
        match = scanner.match()
        while match:
            kind = match.lastgroup
            full_match = match.group(match.lastgroup)
            if with_subgroups:
                subgroups = {
                    k: v for k, v in match.groupdict().items() if v is not None and k != kind
                }
            else:
                subgroups = {}
            tokens.append((kind, full_match, subgroups))
            match = scanner.match()
        return tokens

    def _raise_tokenization_error(self):
        raise SpecTokenizationError(self.literal_str)

    def _raise_parsing_error(self, message):
        raise SpecParsingError(message, None, self.literal_str)

    def next_spec(
        self, initial_spec: Optional["spack.spec.Spec"] = None
    ) -> Optional["spack.spec.Spec"]:
        """Return the next spec parsed from text.

        Args:
            initial_spec: object where to parse the spec. If None a new one
                will be created.

        Return:
            The spec that was parsed
        """
        if not self.match:
            return initial_spec

        if self.match.lastgroup == "UNEXPECTED":
            self._raise_tokenization_error()

        root_spec = self._parse_node(initial_spec)
        current_spec = root_spec

        while self.match:
            if self.match.lastgroup == "DEPENDENCY":
                token = self.match.group()
                # Strip leading whitespace for checking startswith
                token = token.lstrip()
                is_direct = token.startswith("%")
                propagation = PropagationPolicy.NONE
                if is_direct and token.startswith("%%"):
                    propagation = PropagationPolicy.PREFERENCE

                if self.match.group("DEPENDENCY_edge_bracket"):
                    # Advance
                    self.match = self.scanner.match()

                    attributes = {}
                    substitute = None
                    while self.match:
                        if self.match.lastgroup == "KEY_VALUE_PAIR":
                            name = self.match.group("KEY_VALUE_PAIR_kv_name")
                            value = self.match.group("KEY_VALUE_PAIR_kv_value")
                            value = strip_quotes_and_unescape(value)
                            # Split by comma for list values
                            value_list = [v.strip() for v in value.split(",")]
                            attributes[name] = value_list

                            self.match = self.scanner.match()

                        elif self.match.lastgroup == "END_EDGE_PROPERTIES":
                            virtuals_str = self.match.group("END_EDGE_PROPERTIES_virtuals")
                            substitute = self.match.group("END_EDGE_PROPERTIES_substitute")

                            if virtuals_str:
                                virtuals = attributes.get("virtuals", [])
                                virtuals.extend(virtuals_str.split(","))
                                attributes["virtuals"] = virtuals

                            # Advance
                            self.match = self.scanner.match()

                            break
                        else:
                            raise ValueError(
                                f"Unexpected token in edge properties: {self.match.lastgroup}"
                            )

                    depflag = 0
                    if "deptypes" in attributes:
                        depflag = spack.deptypes.canonicalize(attributes["deptypes"])

                    virtuals_tuple = tuple(attributes.get("virtuals", ()))

                    conditions = None
                    if "when" in attributes:
                        when_string = attributes["when"][0]
                        conditions = SpecParser(when_string).next_spec()

                    dep_spec = self._parse_node(initial_name=substitute)

                    if is_direct:
                        target_spec = current_spec
                        if dep_spec.name in LEGACY_COMPILER_TO_BUILTIN:
                            dep_spec.name = LEGACY_COMPILER_TO_BUILTIN[dep_spec.name]
                    else:
                        target_spec = root_spec
                        current_spec = dep_spec

                    target_spec._add_dependency(
                        dep_spec,
                        direct=is_direct,
                        depflag=depflag,
                        virtuals=virtuals_tuple,
                        propagation=propagation,
                        when=conditions,
                    )

                else:
                    virtuals_str = self.match.group("DEPENDENCY_virtuals")
                    substitute = self.match.group("DEPENDENCY_substitute")

                    virtuals_tuple = tuple(virtuals_str.split(",")) if virtuals_str else ()

                    # if no virtual assignment, check for a toolchain - look ahead to find the
                    # toolchain and substitute it
                    advanced = False
                    if not virtuals_tuple and is_direct and self.match:
                        # Peek ahead to see if next token is a package name that's a toolchain
                        next_match = self.scanner.match()
                        if (
                            next_match
                            and next_match.lastgroup == "UNQUALIFIED_PACKAGE_NAME"
                            and next_match.group().strip() in self.toolchains
                        ):
                            toolchain_name = next_match.group().strip()
                            self.match = self.scanner.match()  # Consume the toolchain name
                            self._apply_toolchain(
                                current_spec, toolchain_name, propagation=propagation
                            )
                            continue

                        # If not a toolchain, reset the scanner position
                        self.match = next_match
                        advanced = True

                    # Advance
                    if not advanced:
                        self.match = self.scanner.match()

                    dep_spec = self._parse_node(initial_name=substitute)

                    if is_direct:
                        target_spec = current_spec
                        if dep_spec.name in LEGACY_COMPILER_TO_BUILTIN:
                            dep_spec.name = LEGACY_COMPILER_TO_BUILTIN[dep_spec.name]
                    else:
                        target_spec = root_spec
                        current_spec = dep_spec

                    target_spec._add_dependency(
                        dep_spec,
                        direct=is_direct,
                        depflag=0,
                        virtuals=virtuals_tuple,
                        propagation=propagation,
                    )

            elif self.match.lastgroup == "UNEXPECTED":
                self._raise_tokenization_error()

            else:
                break

        return root_spec

    def _parse_node(
        self, initial_spec: Optional["spack.spec.Spec"] = None, initial_name: Optional[str] = None
    ) -> "spack.spec.Spec":
        """Parse a single spec node"""
        spec = initial_spec
        if spec is None:
            from spack.spec import Spec

            spec = Spec()

        # 1. Package Name
        if initial_name:
            spec.name = initial_name
            if "." in initial_name:
                parts = initial_name.split(".")
                spec.name = parts[-1]
                spec.namespace = ".".join(parts[:-1])
        elif self.match and self.match.lastgroup == "UNQUALIFIED_PACKAGE_NAME":
            if self.match.group() != "*":
                spec.name = self.match.group().strip()
            self.match = self.scanner.match()
        elif self.match and self.match.lastgroup == "UNEXPECTED":
            self._raise_tokenization_error()
        elif self.match and self.match.lastgroup == "FULLY_QUALIFIED_PACKAGE_NAME":
            parts = self.match.group().strip().split(".")
            spec.name = parts[-1]
            spec.namespace = ".".join(parts[:-1])
            self.match = self.scanner.match()
        elif self.match and self.match.lastgroup == "FILENAME":
            file_path = self.match.group().strip()
            file = pathlib.Path(file_path)

            if not file.exists():
                raise spack.error.NoSuchSpecFileError(f"No such spec file: '{file}'")

            with file.open("r", encoding="utf-8") as stream:
                if str(file).endswith(".json"):
                    spec_from_file = spack.spec.Spec.from_json(stream)
                else:
                    spec_from_file = spack.spec.Spec.from_yaml(stream)
            spec._dup(spec_from_file)

            self.match = self.scanner.match()
            return spec

        # 2. Attributes
        has_version = False
        while self.match:
            kind = self.match.lastgroup

            if kind == "VERSION":
                if has_version:
                    raise ValueError("Multiple versions")

                if self.match.group("VERSION_git_version"):
                    spec.versions = spack.version.VersionList(
                        [spack.version.GitVersion(self.match.group("VERSION_git_version"))]
                    )
                else:
                    spec.versions = spack.version.VersionList(
                        self.match.group("VERSION_version_list")
                    )
                spec.attach_git_version_lookup()
                has_version = True

            elif kind == "BOOL_VARIANT":
                prefix = self.match.group("BOOL_VARIANT_bv_prefix")
                name = self.match.group("BOOL_VARIANT_bv_name")
                propagate = len(prefix) == 2
                value = prefix.startswith("+")
                try:
                    spec._add_flag(name, value, propagate, concrete=True)
                except Exception as e:
                    self._raise_parsing_error(str(e))

            elif kind == "KEY_VALUE_PAIR":
                name = self.match.group("KEY_VALUE_PAIR_kv_name")
                sep = self.match.group("KEY_VALUE_PAIR_kv_sep")
                value = self.match.group("KEY_VALUE_PAIR_kv_value")
                propagate = "==" in sep
                concrete = sep.startswith(":")
                try:
                    spec._add_flag(name, strip_quotes_and_unescape(value), propagate, concrete)
                except Exception as e:
                    self._raise_parsing_error(str(e))

            elif kind == "DAG_HASH":
                if spec.abstract_hash:
                    break
                spec.abstract_hash = self.match.group().strip()[1:]

            elif kind == "UNEXPECTED":
                self._raise_tokenization_error()

            else:
                # Stop if we hit something else (like DEPENDENCY or another package name)
                break

            self.match = self.scanner.match()

        return spec

    def _apply_toolchain(
        self, spec: "spack.spec.Spec", name: str, *, propagation: PropagationPolicy
    ) -> None:
        if name not in self.parsed_toolchains:
            toolchain = self._parse_toolchain(name)
            self.parsed_toolchains[name] = toolchain

        propagation_arg = None if propagation != PropagationPolicy.PREFERENCE else propagation
        # Here we need to copy because we want "foo %toolc ^bar %toolc" to generate different
        # objects for the toolc attached to foo and bar, since the solver depends on that to
        # generate facts
        toolchain = self.parsed_toolchains[name].copy(propagation=propagation_arg)
        spec.constrain(toolchain)

    def _parse_toolchain(self, name: str) -> "spack.spec.Spec":
        toolchain_config = self.toolchains[name]
        if isinstance(toolchain_config, str):
            toolchain = parse_one_or_raise(toolchain_config)
            self._ensure_all_direct_edges(toolchain)
        else:
            from spack.spec import Spec

            toolchain = Spec()
            for entry in toolchain_config:
                toolchain_part = parse_one_or_raise(entry["spec"])
                when = entry.get("when", "")
                self._ensure_all_direct_edges(toolchain_part)

                # Conditions are applied to every edge in the constraint
                for edge in toolchain_part.traverse_edges():
                    edge.when.constrain(when)
                toolchain.constrain(toolchain_part)
        return toolchain

    def _ensure_all_direct_edges(self, constraint: "spack.spec.Spec") -> None:
        for edge in constraint.traverse_edges(root=False):
            if not edge.direct:
                raise spack.error.SpecError(
                    f"cannot use '^' in toolchain definitions, and the current "
                    f"toolchain contains '{edge.format()}'"
                )

    def all_specs(self) -> List["spack.spec.Spec"]:
        """Return all the specs that remain to be parsed"""
        return list(iter(self.next_spec, None))
