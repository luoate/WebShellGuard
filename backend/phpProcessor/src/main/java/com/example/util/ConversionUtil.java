package com.example.util;

import com.example.baseListener.PhpParser;
import com.example.model.SimpleNode;
import org.antlr.v4.runtime.ParserRuleContext;
import org.antlr.v4.runtime.Vocabulary;
import org.antlr.v4.runtime.tree.ErrorNode;
import org.antlr.v4.runtime.tree.TerminalNode;

import java.util.ArrayList;
import java.util.List;
import java.util.Stack;

/*
kotlin version is much simple: https://github.com/JetBrains-Research/astminer/blob/master/src/main/kotlin/astminer/parse/antlr/conversionUtil.kt
 */

public class ConversionUtil {

    private static final Vocabulary vocabulary = PhpParser.VOCABULARY;
    private static final String[] ruleNames = PhpParser.ruleNames;

    public static SimpleNode convertAntlrTree(ParserRuleContext tree){
        return convertRuleContext(tree, null);
    }

    // recursively convert Antlr AST to simplified AST
    private static SimpleNode convertRuleContext(ParserRuleContext ruleContext,
                                                SimpleNode parent){
        String typeLabel = ruleNames[ruleContext.getRuleIndex()];
        SimpleNode currentNode = new SimpleNode(typeLabel, parent, null);
        List<SimpleNode> children = new ArrayList<>();

        if (ruleContext.children == null)
            return currentNode;
        ruleContext.children.forEach(it -> {
            if (it instanceof TerminalNode)
                children.add(convertTerminalNode((TerminalNode)it, currentNode));
            else if (it instanceof ErrorNode)
                children.add(convertErrorNode((ErrorNode)it, currentNode));
            else
                children.add(convertRuleContext((ParserRuleContext)it, currentNode));
        });

        currentNode.replaceChildren(children);
        return currentNode;
    }

    // convert error node
    private static SimpleNode convertErrorNode(ErrorNode errorNode,
                                              SimpleNode parent){
        return new SimpleNode(
                            "Error",
                            parent,
                            errorNode.getText()
        );
    }

    // convert terminal node
    private static SimpleNode convertTerminalNode(TerminalNode terminalNode,
                                              SimpleNode parent){
        String curType = vocabulary.getSymbolicName(terminalNode.getSymbol().getType());
        String parentType = parent.getTypeLabel();

        if (parentType.equals("stringConstant") && curType.equals("Label"))
            curType = "stringConstant";

        return new SimpleNode(
                curType,
                parent,
                terminalNode.getSymbol().getText()
        );
    }


    // compute range
//    private static NodeRange getRange(ParserRuleContext ruleContext){
//        return new NodeRange(new Position(ruleContext.getStart().getLine(),
//                                ruleContext.getStart().getCharPositionInLine()),
//                new Position(ruleContext.getStop().getLine(),
//                        ruleContext.getStop().getCharPositionInLine() + ruleContext.getStop().getStopIndex() - ruleContext.getStop().getStartIndex()));
//    }
//
//    private static NodeRange getRange(TerminalNode terminalNode){
//        return new NodeRange(new Position(terminalNode.getSymbol().getLine(),
//                                          terminalNode.getSymbol().getCharPositionInLine()),
//                             new Position(terminalNode.getSymbol().getLine(),
//                                      terminalNode.getSymbol().getCharPositionInLine() +
//                                              terminalNode.getSymbol().getStopIndex()
//                                              - terminalNode.getSymbol().getStartIndex()));
//    }
//
//    private static NodeRange getRange(ErrorNode errorNode){
//        return new NodeRange(new Position(errorNode.getSymbol().getLine(),
//                errorNode.getSymbol().getCharPositionInLine()),
//                new Position(errorNode.getSymbol().getLine(),
//                        errorNode.getSymbol().getCharPositionInLine() +
//                                errorNode.getSymbol().getStopIndex()
//                                - errorNode.getSymbol().getStartIndex()));
//    }


    // simplify AST by PreOrderVisit
//    public static SimpleNode compressTree(SimpleNode root) {
//        if (root == null || root.isLeaf()) {
//            return root;
//        }
//
//        // 使用栈进行迭代处理
//        Stack<SimpleNode> stack = new Stack<>();
//        stack.push(root);
//
//        while (!stack.isEmpty()) {
//            SimpleNode node = stack.pop();
//
//            // 压缩单子节点链
//            while (node.getChildren().size() == 1) {
//                SimpleNode preParent = node.getParent();
//                node = node.getChildren().get(0);
//                node.setParent(preParent);
//            }
//
//            // 将所有子节点压入栈中处理
//            List<SimpleNode> children = node.getChildren();
//            for (SimpleNode child : children) {
//                stack.push(child);
//            }
//
//            // 更新子节点列表（保持接口一致性）
//            List<SimpleNode> newChildren = new ArrayList<>(children);
//            node.replaceChildren(newChildren);
//        }
//
//        // 返回树的根节点（如果根节点被压缩，向上追溯）
//        while (root.getParent() != null) {
//            root = root.getParent();
//        }
//        return root;
//    }
    public static SimpleNode compressTree(SimpleNode root){
        // ignore leaf node
        if (root.isLeaf())
            return root;

        while (root.getChildren().size() == 1){
            SimpleNode preParent = root.getParent();
            root = root.getChildren().get(0);
            root.setParent(preParent);
        }

        List<SimpleNode> newChildren = new ArrayList<>();
        root.getChildren().forEach(child -> {newChildren.add(compressTree(child));});
        root.replaceChildren(newChildren);
        return root;
    }
}
