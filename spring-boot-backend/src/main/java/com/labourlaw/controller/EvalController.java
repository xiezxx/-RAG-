package com.labourlaw.controller;

import com.labourlaw.mapper.ChatHistoryMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;
import javax.servlet.http.HttpServletRequest;
import java.util.*;

@RestController
@RequestMapping("/api/eval")
public class EvalController {

    @Autowired
    private ChatHistoryMapper chatHistoryMapper;

    @Value("${rag.service.url}")
    private String ragServiceUrl;

    /** 消融实验面板数据（仅管理员）：代理 Python /api/eval/ablation（读取 ablation_results.json + 测试题） */
    @GetMapping("/ablation")
    public Map<String, Object> ablation(HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role) && !"RESEARCHER".equals(role))
            return Map.of("code", 403, "message", "仅管理员或研究人员可查看消融实验数据");

        try {
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(5000);
            factory.setReadTimeout(30000);
            Map<?, ?> data = new RestTemplate(factory).getForObject(
                    ragServiceUrl + "/api/eval/ablation", Map.class);
            return Map.of("code", 200, "data", data != null ? data : Map.of());
        } catch (Exception e) {
            return Map.of("code", 500, "message", "消融实验数据暂不可用");
        }
    }

    // ── 问答测试集管理（管理员/研究人员，落盘 Python 侧 test_questions.json） ──

    /** 测试集列表 */
    @GetMapping("/testset")
    public Map<String, Object> testset(HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role) && !"RESEARCHER".equals(role)) return Map.of("code", 403, "message", "权限不足");
        try {
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(5000);
            factory.setReadTimeout(15000);
            List<?> list = new RestTemplate(factory).getForObject(
                    ragServiceUrl + "/api/eval/testset", List.class);
            return Map.of("code", 200, "data", list != null ? list : List.of());
        } catch (Exception e) {
            return Map.of("code", 500, "message", "测试集暂不可用");
        }
    }

    /** 新增测试题 */
    @PostMapping("/testset")
    public Map<String, Object> testsetAdd(@RequestBody Map<String, Object> body, HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role) && !"RESEARCHER".equals(role)) return Map.of("code", 403, "message", "权限不足");
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(5000);
            factory.setReadTimeout(15000);
            Map<?, ?> data = new RestTemplate(factory).postForObject(
                    ragServiceUrl + "/api/eval/testset", entity, Map.class);
            return Map.of("code", 200, "data", data, "message", "已添加");
        } catch (RestClientResponseException e) {
            return Map.of("code", 400, "message", "添加失败：题目格式不正确");
        } catch (Exception e) {
            return Map.of("code", 500, "message", "RAG 服务暂不可用");
        }
    }

    /** 删除测试题 */
    @DeleteMapping("/testset/{id}")
    public Map<String, Object> testsetDelete(@PathVariable String id, HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role) && !"RESEARCHER".equals(role)) return Map.of("code", 403, "message", "权限不足");
        try {
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(5000);
            factory.setReadTimeout(15000);
            new RestTemplate(factory).delete(new java.net.URI(ragServiceUrl + "/api/eval/testset/" + id));
            return Map.of("code", 200, "message", "已删除");
        } catch (RestClientResponseException e) {
            return Map.of("code", 404, "message", "题目不存在");
        } catch (Exception e) {
            return Map.of("code", 500, "message", "RAG 服务暂不可用");
        }
    }

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

    /** 获取问答历史（含评分）。
     *  可见性规则：管理员 = 全员记录；普通用户 = 自己 + 其他普通用户（role='USER'）的记录，不含管理员。 */
    @GetMapping("/history")
    public Map<String, Object> history(@RequestParam(defaultValue = "50") int limit, HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        if (userId == null) return Map.of("code", 401, "message", "未认证");
        String role = (String) request.getAttribute("role");

        limit = Math.max(1, Math.min(limit, 100));
        List<Map<String, Object>> list = "ADMIN".equals(role)
                ? chatHistoryMapper.findAllWithUserJoin(limit)
                : chatHistoryMapper.findByUserRole(limit);
        List<Map<String, Object>> result = new ArrayList<>();
        for (Map<String, Object> row : list) {
            Object rowUserId = row.get("userId");
            row.put("mine", rowUserId != null && rowUserId.toString().equals(String.valueOf(userId)));
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
