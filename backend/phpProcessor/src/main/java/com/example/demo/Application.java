package com.example.demo;

import com.alibaba.fastjson.JSON;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

import com.example.generator.ScriptParser;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(Application.class);
        app.setDefaultProperties(Collections.singletonMap("server.port", "9090"));
        app.run(args);
    }
    public static void generateSequenceFile(String phpFilePath) throws IOException {
        ScriptParser scriptParser = new ScriptParser();
        scriptParser.parse(phpFilePath);
        Map<String, List<String>> sequenceData = new HashMap<>(){
            {
                put("tokenSequence", scriptParser.getTokenSequence().stream().filter(Objects::nonNull).collect(Collectors.toList()));
                put("stringSequence", scriptParser.getStringLiterals());
                put("tags", scriptParser.getTags());
            }
        };

        String jsonStr = JSON.toJSONString(sequenceData);
        System.out.println(jsonStr);
    }
}
