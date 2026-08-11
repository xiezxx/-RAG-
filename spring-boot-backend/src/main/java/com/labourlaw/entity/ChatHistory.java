package com.labourlaw.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class ChatHistory {
    private Long id;
    private Long userId;
    private String question;
    private String answer;
    private String sources;
    private Integer rating;       // 1-5 星评分
    private String feedback;      // 用户反馈
    private LocalDateTime createdAt;
}
