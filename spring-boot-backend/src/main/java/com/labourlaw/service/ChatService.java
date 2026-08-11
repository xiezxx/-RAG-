package com.labourlaw.service;

import com.labourlaw.dto.*;
import com.labourlaw.entity.*;
import com.labourlaw.mapper.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import java.util.*;

@Service
public class ChatService {

    @Autowired
    private ChatHistoryMapper chatHistoryMapper;

    @Value("${rag.service.url}")
    private String ragServiceUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    public ChatResponse chat(ChatRequest request) {
        // 1. 调用 Python RAG 服务（含对话历史）
        String ragUrl = ragServiceUrl + "/api/chat";
        Map<String, Object> ragRequest = new HashMap<>();
        ragRequest.put("question", request.getQuestion());
        ragRequest.put("top_k", 8);
        ragRequest.put("history", request.getHistory() != null ? request.getHistory() : List.of());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(ragRequest, headers);

        ResponseEntity<Map> ragResponse;
        try {
            ragResponse = restTemplate.postForEntity(ragUrl, entity, Map.class);
        } catch (Exception e) {
            ChatResponse errorResp = new ChatResponse();
            errorResp.setAnswer("RAG 服务暂时不可用，请稍后重试。");
            errorResp.setSources(List.of());
            return errorResp;
        }

        Map<String, Object> body = ragResponse.getBody();
        if (body == null) {
            ChatResponse errorResp = new ChatResponse();
            errorResp.setAnswer("RAG 服务返回为空，请稍后重试。");
            errorResp.setSources(List.of());
            return errorResp;
        }
        String answer = (String) body.getOrDefault("answer", "未获取到回答");
        Object rawSources = body.get("sources");
        List<Map<String, String>> sourcesList = rawSources instanceof List
                ? (List<Map<String, String>>) rawSources : List.of();

        // 2. 组装响应
        ChatResponse resp = new ChatResponse();
        resp.setAnswer(answer);
        List<ChatResponse.SourceItem> sourceItems = new ArrayList<>();
        for (Map<String, String> s : sourcesList) {
            ChatResponse.SourceItem item = new ChatResponse.SourceItem();
            item.setType(s.getOrDefault("type", "unknown"));
            item.setTitle(s.getOrDefault("title", ""));
            item.setSnippet(s.getOrDefault("snippet", ""));
            sourceItems.add(item);
        }
        resp.setSources(sourceItems);

        // 3. 保存对话历史
        ChatHistory history = new ChatHistory();
        history.setUserId(request.getUserId());
        history.setQuestion(request.getQuestion());
        history.setAnswer(answer);
        // JSON 序列化 sources
        try {
            com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            history.setSources(mapper.writeValueAsString(sourceItems));
        } catch (Exception e) {
            history.setSources("[]");
        }
        chatHistoryMapper.insert(history);

        return resp;
    }

    public List<ChatHistory> getHistory(Long userId, int limit) {
        return chatHistoryMapper.findByUserId(userId, limit);
    }
}
