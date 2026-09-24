package com.example.demo.controller;

import com.alibaba.fastjson.JSON;
import com.example.generator.ScriptParser;
import org.springframework.web.bind.annotation.*;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = {"http://localhost:8848","http://localhost:8849", "http://localhost:11451"})  // 允许特定域名访问
public class ParserController  {
    @PostMapping("/parser")
    public String parser(@RequestBody byte[] phpFileByte) throws IOException {
        String receivedString = new String(phpFileByte, StandardCharsets.UTF_8);
//        System.out.println(receivedString);
//        System.out.println(Arrays.toString(phpFileString));
//        phpFileString = phpFileString.substring(9, phpFileString.length() - 2).replaceAll("\\\\n", "\n").replaceAll("\\\\\"", "\"");
//        System.out.println(phpFileString);
//        phpFileString = "<?php\n$password = \"LandGrey\";";
//        System.out.println(phpFileString);
        ScriptParser scriptParser = new ScriptParser();
        InputStream content = new ByteArrayInputStream(phpFileByte);
        // 创建文件并写入内容
//        try (FileWriter writer = new FileWriter("tmp")) {
//            writer.write(phpFileString);
//            System.out.println("文件创建并写入成功: " + "tmp");
//        } catch (IOException e) {
//            System.out.println("文件写入失败: " + e.getMessage());
//        }
        scriptParser.parse(content);

        Map<String, List<String>> sequenceData = new HashMap<>() {{
            put("tokenSequence", scriptParser.getTokenSequence().stream().filter(Objects::nonNull).collect(Collectors.toList()));
            put("stringSequence", scriptParser.getStringLiterals());
            put("tags", scriptParser.getTags());
        }};

        String jsonStr = JSON.toJSONString(sequenceData);
//        System.out.println(jsonStr);
        return jsonStr;
    }
}
