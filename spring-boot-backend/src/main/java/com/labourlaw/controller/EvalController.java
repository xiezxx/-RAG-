package com.labourlaw.controller;

import com.labourlaw.entity.ChatHistory;
import com.labourlaw.mapper.ChatHistoryMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import javax.servlet.http.HttpServletRequest;
import java.util.*;

@RestController
@RequestMapping("/api/eval")
public class EvalController {

    @Autowired
    private ChatHistoryMapper chatHistoryMapper;

    /** 提交回答满意度评价 */
    @PostMapping("/feedback")
    public Map<String, Object> feedback(@RequestBody Map<String, Object> body, HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        if (userId == null) return Map.of("code", 401, "message", "未认证");

        Long chatId = body.get("chatId") != null ? Long.valueOf(body.get("chatId").toString()) : null;
        Integer rating = null;
        if (body.get("rating") != null) {
            try {
                rating = Integer.valueOf(body.get("rating").toString());
            } catch (NumberFormatException ignored) {
                return Map.of("code", 400, "message", "rating 必须是数字");
            }
        }
        String comment = (String) body.getOrDefault("comment", "");

        if (chatId == null || rating == null) {
            return Map.of("code", 400, "message", "请提供 chatId 和 rating");
        }

        int rows = chatHistoryMapper.updateRating(chatId, userId, rating, comment);
        if (rows == 0) return Map.of("code", 404, "message", "记录不存在");
        return Map.of("code", 200, "message", "反馈已提交");
    }

    /** 获取问答历史（含评分） */
    @GetMapping("/history")
    public Map<String, Object> history(@RequestParam(defaultValue = "50") int limit, HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        if (userId == null) return Map.of("code", 401, "message", "未认证");

        limit = Math.max(1, Math.min(limit, 100));
        List<ChatHistory> list = chatHistoryMapper.findByUserId(userId, limit);
        List<Map<String, Object>> result = new ArrayList<>();
        for (ChatHistory ch : list) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id", ch.getId());
            row.put("question", ch.getQuestion());
            row.put("answer", ch.getAnswer());
            row.put("sources", ch.getSources());
            row.put("rating", ch.getRating());
            row.put("feedback", ch.getFeedback());
            row.put("createdAt", ch.getCreatedAt());
            result.add(row);
        }
        return Map.of("code", 200, "data", result);
    }

    /** 管理员查看所有用户的问答历史（含反馈） */
    @GetMapping("/admin/history")
    public Map<String, Object> adminHistory(@RequestParam(defaultValue = "100") int limit, HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");

        limit = Math.max(1, Math.min(limit, 500));
        List<Map<String, Object>> list = chatHistoryMapper.findAllWithUserJoin(limit);
        return Map.of("code", 200, "data", list);
    }

    /** 管理员查看评估统计 */
    @GetMapping("/stats")
    public Map<String, Object> stats(HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("totalQuestions", chatHistoryMapper.count());

        Double avg = chatHistoryMapper.avgRating();
        stats.put("avgRating", avg != null ? Math.round(avg * 100.0) / 100.0 : 0);

        stats.put("ratingDistribution", chatHistoryMapper.ratingDistribution());
        return Map.of("code", 200, "data", stats);
    }
}
