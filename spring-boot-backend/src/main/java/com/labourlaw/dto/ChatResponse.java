package com.labourlaw.dto;

import java.util.List;

public class ChatResponse {
    private String answer;
    private List<SourceItem> sources;

    public String getAnswer() { return answer; }
    public void setAnswer(String answer) { this.answer = answer; }
    public List<SourceItem> getSources() { return sources; }
    public void setSources(List<SourceItem> sources) { this.sources = sources; }

    public static class SourceItem {
        private String type;
        private String title;
        private String snippet;

        public String getType() { return type; }
        public void setType(String type) { this.type = type; }
        public String getTitle() { return title; }
        public void setTitle(String title) { this.title = title; }
        public String getSnippet() { return snippet; }
        public void setSnippet(String snippet) { this.snippet = snippet; }
    }
}
