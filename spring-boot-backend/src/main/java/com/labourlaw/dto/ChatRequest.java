package com.labourlaw.dto;

import java.util.List;
import java.util.Map;

public class ChatRequest {
    private String question;
    private Long userId;
    private List<Map<String, String>> history;  // [{"role":"user/assistant","content":"..."}]

    public String getQuestion() { return question; }
    public void setQuestion(String question) { this.question = question; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public List<Map<String, String>> getHistory() { return history; }
    public void setHistory(List<Map<String, String>> history) { this.history = history; }
}
