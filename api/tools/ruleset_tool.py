import json
import re

from marshmallow import ValidationError

from common_utils import logger
from model.seclang_model import (
    SecAction,
    SecBaseSchema,
    SecComponentSignature,
    SecMarker,
    SecRule,
    DataObjectSchema,
)


# noinspection PyMethodMayBeStatic,PyListCreation
class RuleSetParser:
    lines = []
    line_index = 0
    c_line = 0

    def __init__(self, base_path):
        self.base_path = base_path
        self.charset = "utf-8"

    def _is_com_break(self, cmd):
        b = cmd.startswith(
            (
                "SecRule",
                "SecMarker",
                "SecAction",
                "SecDefaultAction",
                "SecComponentSignature",
                "SecResponseBodyAccess",
                "#",
            )
        )
        return b

    def _parse_comment(self):
        com = ""
        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]
            if line.startswith("#"):
                com += line[1:]
                self.line_index += 1
            else:
                break
        return com

    def _parse_signature(self, line) -> SecComponentSignature:
        m = SecComponentSignature().load(
            {"schema_type": "SecComponentSignature", "text": line.split('"')[1]}
        )
        self.line_index += 1
        return m

    def _parse_marker(self, line) -> SecMarker:
        m = SecMarker().load({"schema_type": "SecMarker", "text": line.split('"')[1]})
        self.line_index += 1
        return m

    def _parse_action(self, line) -> SecAction:
        a = SecAction().load(
            {"schema_type": "SecAction", "t": [], "setvar": [], "initcol": []}
        )

        pattern = re.compile('"(.*)"')
        matcher = pattern.search(line)

        if matcher:
            rule_content = matcher.group(1)
            if rule_content:
                vars_list = rule_content.split(",")
                for token in vars_list:
                    key_pair = token.strip().split(":")
                    key_pair[0] = key_pair[0].strip()
                    if len(key_pair) > 1:
                        key_pair[1] = key_pair[1].strip()
                        if key_pair[0] == "id":
                            a["code"] = int(key_pair[1])
                        elif key_pair[0] == "initcol":
                            a["initcol"].append(key_pair[1])
                        elif key_pair[0] == "ver":
                            a["version"] = key_pair[1]
                        elif key_pair[0] == "t":
                            a["t"].append(key_pair[1])
                        elif key_pair[0] == "phase":
                            a["phase"] = int(key_pair[1])
                        elif key_pair[0] == "setvar":
                            a["setvar"].append(key_pair[1])
                        else:
                            logger.error(
                                f"parseRule Unknown key [{key_pair[0]}] from {line}"
                            )
                    else:
                        if key_pair[0].lower() in ["pass", "deny", "block", "config"]:
                            a["action"] = key_pair[0]
                        elif "audit" in key_pair[0]:
                            a["audit_log"] = key_pair[0]
                        elif "log" in key_pair[0]:
                            a["logging"] = key_pair[0]

        self.line_index += 1
        return a

    def _parse_scope(self, scope):
        return [s.strip() for s in scope.split("|")]

    def _parse_rule(self, line) -> SecRule:
        fi = line.index(" ")
        rule = SecRule().load(
            {
                "schema_type": "SecRule",
                "t": [],
                "ctl": [],
                "scope": self._parse_scope(line[fi : line.index(" ", fi + 1)]),
                "tags": [],
                "setvar": [],
                "expirevar": [],
                "files": [],
                "chain_starter": False,
                "chain": [],
            }
        )

        rule_data = line[line.index(" ", fi + 1) :]
        regex = re.compile('"(.*?)(?<!\\\\)"(?:\\s+"(.*)")?')

        matcher = regex.search(rule_data)
        if matcher:
            rule["condition"] = matcher.group(1)
            rule["files"] = self._parse_from_file(rule["condition"])
            rule_content = matcher.group(2)
            if rule_content:
                for token in re.split(",(?=(?:[^']*'[^']*')*[^']*$)", rule_content):
                    key_pair = re.split(":(?=(?:[^']*'[^']*')*[^']*$)", token)

                    if len(key_pair) > 1:
                        key = key_pair[0].strip()
                        if key == "id":
                            rule["code"] = int(key_pair[1])
                        elif key == "ver":
                            rule["version"] = key_pair[1]
                        elif key == "phase":
                            rule["phase"] = int(key_pair[1])
                        elif key == "tag":
                            rule["tags"].append(key_pair[1])
                        elif key == "t":
                            rule["t"].append(str(key_pair[1]))
                        elif key == "setvar":
                            rule["setvar"].append(key_pair[1])
                        elif key == "expirevar":
                            rule["expirevar"].append(key_pair[1])
                        elif key == "logdata":
                            rule["logdata"] = key_pair[1]
                        elif key == "ctl":
                            rule["ctl"].append(key_pair[1])
                        elif key == "msg":
                            rule["msg"] = key_pair[1]
                        elif key == "skipAfter":
                            rule["skip_after"] = key_pair[1]
                        elif key == "severity":
                            rule["severity"] = key_pair[1]
                        elif key == "status":
                            rule["status"] = int(key_pair[1])
                        else:
                            logger.error(
                                f"parseRule Unknown key [{key}/{key_pair[1]}] from {line}"
                            )
                    else:
                        token = token.strip().replace(",", "")
                        if token.lower() in ["pass", "deny", "block", "config"]:
                            rule["action"] = token
                        elif "audit" in token:
                            rule["audit_log"] = token
                        elif "log" in token:
                            rule["logging"] = token
                        elif token.lower() == "multimatch":
                            rule["multi_match"] = True
                        elif token.lower() == "chain":
                            rule["chain_starter"] = True
                        elif token.lower() == "capture":
                            rule["capture"] = True
                        else:
                            logger.error(
                                f"parseRule Unknown token [{token}] from {rule_content}"
                            )

        self.line_index += 1
        logger.debug(rule)

        return rule

    def _parse_from_file(self, source):
        dts = []

        if source:
            pattern = re.compile(r"@(pmFromFile|ipMatchFromFile|pmf) (.*)")
            m = pattern.search(source)
            if m:
                for val in m.group(2).split(" "):
                    if val:
                        data_lines = []
                        with open(
                            f"{self.base_path}/{val}", "r", encoding=self.charset
                        ) as file:
                            for line in file:
                                if not line.startswith("#"):
                                    data_lines.append(line.strip())
                        try:
                            dt = DataObjectSchema().load(
                                {
                                    "name": val.strip(),
                                    "content": data_lines,
                                }
                            )
                            dts.append(dt)
                        except ValidationError as e:
                            logger.error(f"Object load failed: {e.messages}")
        return dts

    def load_file(self, ruleset_name):
        e_lines = []
        self.c_line = 0
        with open(f"{self.base_path}/{ruleset_name}", "r", encoding="utf-8") as arq:
            file_content = arq.readlines()
            for line in file_content:
                self.c_line += 1
                r = ""
                line = line.rstrip("\r\n").strip()
                if line is not None and len(line) > 2:
                    if line.endswith("\\"):
                        r = line[:-1]
                    else:
                        r = line
                e_lines.append(r.lstrip())

        read_lines = []
        while e_lines:
            line = e_lines.pop(0)
            while e_lines:
                r_line = e_lines.pop(0)
                if self._is_com_break(r_line):
                    e_lines = [r_line] + e_lines
                    read_lines.append(line)
                    break
                else:
                    line += " " + r_line
            if len(line) > 1:
                read_lines.append(line)
        return read_lines

    def read_file_as_seclang(self, ruleset_name):
        logger.debug(ruleset_name)
        self.lines = self.load_file(ruleset_name)
        self.line_index = 0
        ruleset = []
        comment = ""
        chain_starter = False
        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]
            self.line_index += 1
            if line.startswith("#"):
                comment = self._parse_comment()
            else:
                key = line.split(" ")[0]
                if key == "SecMarker":
                    m = self._parse_marker(line)
                    ruleset.append(m)
                elif key == "SecComponentSignature":
                    s = self._parse_signature(line)
                    ruleset.append(s)
                elif key == "SecAction":
                    a = self._parse_action(line)
                    ruleset.append(a)
                elif key == "SecRule":
                    r = self._parse_rule(line)
                    if chain_starter:
                        ruleset[-1]["chain"].append(r)
                    else:
                        r["comment"] = comment
                        ruleset.append(r)
                    chain_starter = r["chain_starter"]
                else:
                    logger.error(f"parseFile Unknown key [{key}] from {line}")
        logger.debug(f"{ruleset_name} {self.c_line}/{len(self.lines)}/{len(ruleset)}")
        return ruleset

    @classmethod
    def as_seclang(cls, o, ruleset_path=None):

        if o["schema_type"] == "SecComponentSignature":
            return f"SecComponentSignature \"{o['text']}\""

        if o["schema_type"] == "SecMarker":
            return f"SecMarker \"{o['text']}\""

        if o["schema_type"] == "SecRule":
            sb = ["SecRule "]
            sb.append(f"|".join(o["scope"]) + " ")
            sb.append(f"\"{o['condition']}\" ")

            sbr = []
            if "files" in o and ruleset_path:
                for f in o["files"]:
                    with open(f"{ruleset_path}/{f['name']}", "w") as file_data:
                        file_data.write("\n".join(f["content"]))
            if "code" in o:
                sbr.append(f"id:{o['code']}")
            if "version" in o:
                sbr.append(f"ver:{o['version']}")
            if "severity" in o:
                sbr.append(f"severity:{o['severity']}")
            if "phase" in o:
                sbr.append(f"phase:{o['phase']}")
            if "action" in o:
                sbr.append(f"{o['action']}")
            if "multiMatch" in o:
                sbr.append(f"multiMatch:{o['multi_match']}")
            if "chain_starter" in o and o["chain_starter"]:
                sbr.append(f"chain")
            if "capture" in o and o["capture"]:
                sbr.append(f"capture")
            if "logging" in o:
                sbr.append(f"{o['logging']}")
            if "audit_log" in o:
                sbr.append(f"{o['audit_log']}")
            if "t" in o:
                for t in o["t"]:
                    sbr.append(f"t:{t}")
            if "ctl" in o:
                for ctl in o["ctl"]:
                    sbr.append(f"ctl:{ctl}")
            if "skip_after" in o:
                sbr.append(f"skipAfter:{o['skip_after']}")
            if "msg" in o:
                sbr.append(f"msg:{o['msg']}")
            if "logdata" in o:
                sbr.append(f"logdata:{o['logdata']}")
            if "tag" in o:
                for tag in o["tag"]:
                    sbr.append(f"tag:{tag}")
            if "setvar" in o:
                for setvar in o["setvar"]:
                    sbr.append(f"setvar:{setvar}")
            sec_rule = ",".join(sbr)
            sb.append(f'"{sec_rule}"')

            if "chain" in o:
                for c in o["chain"]:
                    sb.append(f"\n{cls.as_seclang(c)}")
            rule = "".join(sb)
            return rule

        if o["schema_type"] == "SecAction":
            sb = ["SecAction "]
            sba = []
            if "code" in o:
                sba.append(f"id:{o['code']}")
            if "phase" in o:
                sba.append(f"phase:{o['phase']}")
            if "version" in o:
                sba.append(f"ver:{o['version']}")
            if "action" in o:
                sba.append(f"{o['action']}")
            if "logging" in o:
                sba.append(f"{o['logging']}")
            if "audit_log" in o:
                sba.append(f"{o['audit_log']}")
            if "t" in o:
                for t in o["t"]:
                    sba.append(f"t:{t}")
            if "setvar" in o:
                for setvar in o["setvar"]:
                    sba.append(f"setvar:{setvar}")
            if "initcol" in o:
                for t in o["initcol"]:
                    sba.append(f"initcol:{t}")
            sec_action = ",".join(sba)
            sb.append(f'"{sec_action}"')
            action = "".join(sb)
            return action

    @classmethod
    def load(cls, o):
        schema_type = SecBaseSchema.schema_class(o["schema_type"])
        schema = schema_type()
        return schema.load(o)

    @classmethod
    def dumps(cls, cat):
        rules = cat.pop("rules")
        json_data = json.dumps(cat)
        json_data = json_data[:-1]
        json_data += ',"rules":['
        for r in rules:
            r_type = r["schema_type"]
            schema_type = SecBaseSchema.schema_class(r_type)
            schema = schema_type()
            if r_type == "SecRule":
                chain = r.pop("chain")
                json_data += schema.dumps(r)
                json_data = json_data[:-1]
                if chain:
                    json_data += ',"chain":['
                    for c in chain:
                        json_data += schema.dumps(c) + ","
                    json_data = json_data[:-1] + "]"
                json_data += "},"
            else:
                json_data += schema.dumps(r) + ","
        json_data = json_data[:-1]
        json_data += "]"
        json_data += "}"
        return json_data
