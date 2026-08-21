package com.labourlaw.entity;

import lombok.Data;

@Data
public class PopularizationArticle {
    private Long id;
    private String title;
    private String category;
    private String description;
    private String searchQuery;        // 预写检索词串
    private String content;            // LLM 生成的 markdown 文章
    private String sources;            // JSON 字符串 [{type,title,snippet,status}]
    // 注意：本项目 TIMESTAMP 列无法映射到 LocalDateTime（既有全局问题），用 String 接收
    private String generatedAt;
    private String createdAt;
}
