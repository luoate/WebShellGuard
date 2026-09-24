package com.example;


import org.apache.commons.cli.*;

import java.io.*;

public class Main {

    public static void main(String[] args) throws ParseException, IOException {
//        generateSequenceFile();
//        generateSequenceFile2(new String[] {"-f", "C:\\Users\\lowi\\Desktop\\1.php"});
//        FileProcessor.generateSequenceFile("C:\\Users\\lowi\\Downloads\\dataset\\webshell\\dest\\black_1e27445f0db8615dbe1816fb82105903.php", "C:\\Users\\lowi\\Downloads\\dataset\\webshell\\1.json");
        FileProcessor.processDirectoryFiles("C:\\Users\\lowi\\Downloads\\dataset\\normal\\dest", "C:\\Users\\lowi\\PycharmProjects\\MSDetector-master\\phpProcessor\\files\\sequence\\train\\normal");
//        FileProcessor.generateSequenceFile("C:\\Users\\lowi\\Downloads\\dataset\\webshell\\tobig\\black_a982a93b44ebb774ee5246a77f2c65bf.php", "C:\\Users\\lowi\\Downloads\\dataset\\webshell\\tobig\\1.json");
    }
}
