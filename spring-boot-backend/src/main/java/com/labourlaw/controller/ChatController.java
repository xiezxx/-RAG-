package com.labourlaw.controller;

import com.labourlaw.dto.*;
import com.labourlaw.entity.*;
import com.labourlaw.mapper.*;
import com.labourlaw.service.ChatService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.*;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    @Autowired
    private ChatService chatService;

    @Autowired
    private OperationLogMapper logMapper;

    @Autowired
    private StatuteMapper statuteMapper;

    @Autowired
    private ChatHistoryMapper chatHistoryMapper;

    @Value("${rag.service.url}")
    private String ragServiceUrl;

    @PostMapping("/ask")
    public Map<String, Object> ask(@RequestBody ChatRequest request,
                                   HttpServletRequest httpRequest) {
        try {
            if (request == null || request.getQuestion() == null || request.getQuestion().trim().isEmpty()) {
                return Map.of("code", 400, "message", "问题不能为空");
            }
            if (request.getQuestion().length() > 4000) {
                return Map.of("code", 400, "message", "问题长度不能超过 4000 个字符");
            }
            // 检索模式切换仅管理员可用（普通用户固定完整混合检索）
            String role = (String) httpRequest.getAttribute("role");
            if (!"ADMIN".equals(role) && request.getMode() != null && !request.getMode().isBlank() && !"full".equals(request.getMode())) {
                return Map.of("code", 403, "message", "仅管理员可切换检索模式");
            }
            Long userId = (Long) httpRequest.getAttribute("userId");
            if (userId != null) {
                request.setUserId(userId);
            }
            ChatResponse resp = chatService.chat(request);

            // 操作日志
            try {
                OperationLog log = new OperationLog();
                log.setUserId(userId);
                log.setUsername((String) httpRequest.getAttribute("username"));
                log.setAction("智能问答");
                String q = request.getQuestion();
                log.setTarget(q != null && q.length() > 80 ? q.substring(0, 80) : q);
                log.setIp(httpRequest.getRemoteAddr());
                logMapper.insert(log);
            } catch (Exception ignored) {}

            return Map.of("code", 200, "data", resp, "message", "OK");
        } catch (Exception e) {
            return Map.of("code", 500, "message", "服务暂时不可用，请稍后重试");
        }
    }

    /** 流式问答 — 代理 SSE 流到 Python RAG 服务 */
    @PostMapping("/ask/stream")
    public void askStream(@RequestBody ChatRequest request,
                          HttpServletRequest httpRequest,
                          HttpServletResponse response) throws IOException {
        Long userId = (Long) httpRequest.getAttribute("userId");
        if (userId != null) request.setUserId(userId);

        // 检索模式切换仅管理员可用（普通用户固定完整混合检索）
        String role = (String) httpRequest.getAttribute("role");
        if (!"ADMIN".equals(role) && request.getMode() != null && !request.getMode().isBlank() && !"full".equals(request.getMode())) {
            response.setStatus(403);
            response.setContentType("application/json");
            response.setCharacterEncoding("UTF-8");
            response.getWriter().write("{\"code\":403,\"message\":\"仅管理员可切换检索模式\"}");
            return;
        }

        // 设置 SSE 响应头
        response.setContentType("text/event-stream");
        response.setCharacterEncoding("UTF-8");
        response.setHeader("Cache-Control", "no-cache");
        response.setHeader("Connection", "keep-alive");
        response.setHeader("X-Accel-Buffering", "no");

        // 构建请求体
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("question", request.getQuestion());
        body.put("history", request.getHistory() != null ? request.getHistory() : List.of());
        body.put("top_k", 8);
        if (request.getMode() != null && !request.getMode().isBlank()) {
            body.put("mode", request.getMode());
        }
        String requestBody = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(body);

        // 连接 Python RAG SSE 端点
        URL url = new URL(ragServiceUrl + "/api/chat/stream");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setConnectTimeout(30000);
        conn.setReadTimeout(120000);

        try (OutputStream os = conn.getOutputStream()) {
            os.write(requestBody.getBytes("UTF-8"));
            os.flush();
        }

        // 逐行转发 SSE 流
        com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        StringBuilder fullAnswer = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"))) {
            PrintWriter writer = response.getWriter();
            String line;
            while ((line = reader.readLine()) != null) {
                writer.println(line);
                writer.flush();
                // 收集完整答案用于保存历史（跳过 JSON 控制消息）
                if (line.startsWith("data: ") && !line.contains("__sources__") && !line.equals("data: [DONE]")) {
                    try {
                        String token = mapper.readValue(line.substring(6), String.class);
                        fullAnswer.append(token);
                    } catch (Exception ignored) {}
                }
            }
        } catch (Exception e) {
            response.getWriter().println("data: \"服务暂时不可用，请稍后重试\"\n\ndata: [DONE]\n");
        } finally {
            conn.disconnect();
        }

        // 保存对话历史
        try {
            ChatHistory history = new ChatHistory();
            history.setUserId(userId);
            history.setQuestion(request.getQuestion());
            history.setAnswer(fullAnswer.toString());
            history.setSources("[]");
            chatHistoryMapper.insert(history);
        } catch (Exception ignored) {}

        // 操作日志
        try {
            OperationLog log = new OperationLog();
            log.setUserId(userId);
            log.setUsername((String) httpRequest.getAttribute("username"));
            log.setAction("智能问答(流式)");
            String q = request.getQuestion();
            log.setTarget(q != null && q.length() > 80 ? q.substring(0, 80) : q);
            log.setIp(httpRequest.getRemoteAddr());
            logMapper.insert(log);
        } catch (Exception ignored) {}
    }

    @GetMapping("/history")
    public Map<String, Object> history(
            @RequestParam(defaultValue = "20") int limit,
            HttpServletRequest httpRequest) {
        Long userId = (Long) httpRequest.getAttribute("userId");
        if (userId == null) {
            return Map.of("code", 401, "message", "未认证");
        }
        limit = Math.max(1, Math.min(limit, 100));
        List<ChatHistory> list = chatService.getHistory(userId, limit);
        return Map.of("code", 200, "data", list);
    }

    /** 知识库统计 */
    @GetMapping("/stats")
    public Map<String, Object> stats() {
        Map<String, Object> neo4j = new LinkedHashMap<>();
        neo4j.put("statutes", statuteMapper.count());

        // articles 通过 SUM(article_count) 计算，仍用 ChatHistoryMapper 中查 labour_cases
        List<Statute> all = statuteMapper.findAll();
        int totalArticles = all.stream().mapToInt(s -> s.getArticleCount() != null ? s.getArticleCount() : 0).sum();
        neo4j.put("articles", totalArticles);
        neo4j.put("cases", chatHistoryMapper.countCases());
        neo4j.put("courts", chatHistoryMapper.countDistinctCourts());

        return Map.of("code", 200, "neo4j", neo4j);
    }
}
