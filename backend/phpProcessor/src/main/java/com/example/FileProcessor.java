package com.example;

import com.alibaba.fastjson.JSON;
import com.example.generator.ScriptParser;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Collectors;

public class FileProcessor {
    public static void processDirectoryFiles(String inputDir, String outputDir) throws IOException {
        File dir = new File(inputDir);
        File[] files = dir.listFiles();

        if (files == null || files.length == 0) {
            System.out.println("目录为空或不存在");
            return;
        }

        // 确保目标目录存在
        Files.createDirectories(Paths.get(outputDir));

        int fileIndex = 1;
        for (File file : files) {
            if (file.isFile()) {
                String outputFilePath = outputDir + File.separator + fileIndex + ".json";
//                System.out.println(file.getAbsolutePath());
                generateSequenceFile(file.getAbsolutePath(), outputFilePath);
                fileIndex++;
            }
        }
    }

    public static void generateSequenceFile(String phpFilePath, String seqPath) throws IOException {
        ScriptParser scriptParser = new ScriptParser();
//        scriptParser.parse(phpFilePath);
        try {
            scriptParser.parse(phpFilePath);
        } catch (StackOverflowError e) {
            System.out.println(phpFilePath);
            return;
        }
        Map<String, List<String>> sequenceData = new HashMap<>() {{
            put("tokenSequence", scriptParser.getTokenSequence().stream().filter(Objects::nonNull).collect(Collectors.toList()));
            put("stringSequence", scriptParser.getStringLiterals());
            put("tags", scriptParser.getTags());
        }};

        String jsonStr = JSON.toJSONString(sequenceData);

        try (FileWriter writer = new FileWriter(seqPath)) {
            writer.write(jsonStr);
        } catch (IOException e) {
            e.printStackTrace();
        }

//        System.out.println("文件已保存: " + seqPath);
    }
}
