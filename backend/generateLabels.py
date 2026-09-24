# # 1. 标签和数字的映射
# label_strings = [
#     "SeaWhitespace", "HtmlText", "XmlStart", "PHPStart", "HtmlScriptOpen",
#     "HtmlStyleOpen", "HtmlComment", "HtmlDtd", "HtmlOpen", "Shebang",
#     "Error", "XmlText", "XmlClose", "PHPStartInside", "HtmlClose",
#     "HtmlSlashClose", "HtmlSlash", "HtmlEquals", "HtmlStartQuoteString",
#     "HtmlStartDoubleQuoteString", "HtmlHex", "HtmlDecimal", "HtmlSpace",
#     "HtmlName", "ErrorInside", "PHPStartInsideQuoteString",
#     "HtmlEndQuoteString", "HtmlQuoteString", "ErrorHtmlQuote",
#     "PHPStartDoubleQuoteString", "HtmlEndDoubleQuoteString",
#     "HtmlDoubleQuoteString", "ErrorHtmlDoubleQuote", "ScriptText",
#     "ScriptClose", "PHPStartInsideScript", "StyleBody", "PHPEnd",
#     "Whitespace", "MultiLineComment", "SingleLineComment",
#     "ShellStyleComment", "Abstract", "Array", "As", "BinaryCast",
#     "BoolType", "BooleanConstant", "Break", "Callable", "Case", "Catch",
#     "Class", "Clone", "Const", "Continue", "Declare", "Default", "Do",
#     "DoubleCast", "DoubleType", "Echo", "Else", "ElseIf", "Empty",
#     "EndDeclare", "EndFor", "EndForeach", "EndIf", "EndSwitch", "EndWhile",
#     "Eval", "Exit", "Extends", "Final", "Finally", "FloatCast", "For",
#     "Foreach", "Function", "Global", "Goto", "If", "Implements", "Import",
#     "Include", "IncludeOnce", "InstanceOf", "InsteadOf", "Int8Cast",
#     "Int16Cast", "Int64Type", "IntType", "Interface", "IsSet", "List",
#     "LogicalAnd", "LogicalOr", "LogicalXor", "Namespace", "New", "Null",
#     "ObjectType", "Parent_", "Partial", "Print", "Private", "Protected",
#     "Public", "Require", "RequireOnce", "Resource", "Return", "Static",
#     "StringType", "Switch", "Throw", "Trait", "Try", "Typeof", "UintCast",
#     "UnicodeCast", "Unset", "Use", "Var", "While", "Yield", "From",
#     "LambdaFn", "Get", "Set", "Call", "CallStatic", "Constructor",
#     "Destruct", "Wakeup", "Sleep", "Autoload", "IsSet__", "Unset__",
#     "ToString__", "Invoke", "SetState", "Clone__", "DebugInfo",
#     "Namespace__", "Class__", "Traic__", "Function__", "Method__", "Line__",
#     "File__", "Dir__", "Spaceship", "Lgeneric", "Rgeneric", "DoubleArrow",
#     "Inc", "Dec", "IsIdentical", "IsNoidentical", "IsEqual", "IsNotEq",
#     "IsSmallerOrEqual", "IsGreaterOrEqual", "PlusEqual", "MinusEqual",
#     "MulEqual", "Pow", "PowEqual", "DivEqual", "Concaequal", "ModEqual",
#     "ShiftLeftEqual", "ShiftRightEqual", "AndEqual", "OrEqual", "XorEqual",
#     "BooleanOr", "BooleanAnd", "NullCoalescing", "NullCoalescingEqual",
#     "ShiftLeft", "ShiftRight", "DoubleColon", "ObjectOperator",
#     "NamespaceSeparator", "Ellipsis", "Less", "Greater", "Ampersand",
#     "Pipe", "Bang", "Caret", "Plus", "Minus", "Asterisk", "Percent",
#     "Divide", "Tilde", "SuppressWarnings", "Dollar", "Dot", "QuestionMark",
#     "OpenRoundBracket", "CloseRoundBracket", "OpenSquareBracket",
#     "CloseSquareBracket", "OpenCurlyBracket", "CloseCurlyBracket", "Comma",
#     "Colon", "SemiColon", "Eq", "Quote", "BackQuote", "VarName", "Label",
#     "Octal", "Decimal", "Real", "Hex", "Binary", "BackQuoteString",
#     "SingleQuoteString", "DoubleQuote", "StartNowDoc", "StartHereDoc",
#     "ErrorPhp", "CurlyDollar", "UnicodeEscape", "StringPart", "Comment",
#     "PHPEndSingleLineComment", "CommentEnd", "HereDocText", "XmlText2",
#     "START", "END", "FuncCall", "String", "FuncName", "ClassName", "modifier",
#     "attributes", "integerConstant", "formalParameterList", "O", "boolConstant",
#     "floatConstant", "innerStatementList", "statement", "expression", "innerStatement",
#     "namespaceNameList", "constant", "variableInitializer"
# ]
import json
with open("labels.json", 'r', encoding='utf-8') as file:
    label_strings = json.load(file)
# 2. 生成 label_dict
label_dict = {label: idx for idx, label in enumerate(label_strings)}

# 3. 输出 label_dict
print("Label Dict:", label_dict)

# 4. 保存 label_dict 到 JSON 文件
import json
with open("label_dict.json", "w") as f:
    json.dump(label_dict, f, indent=4)

# 5. 保存标签列表到文本文件
# with open("labels.json", "w") as f:
#     json.dump(label_strings, f, indent=4)

# 结果：label_dict 会被打印并且保存到文件中，标签会被保存在 labels.txt 文件中
