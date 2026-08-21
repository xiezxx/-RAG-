package com.labourlaw.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.labourlaw.entity.DiagnosisReport;
import com.labourlaw.mapper.DiagnosisReportMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;

import javax.servlet.http.HttpServletRequest;
import java.util.*;

/**
 * 智能案情诊断 — 代理 Python /api/diagnosis（RAG 检索 + LLM 诊断报告 + 程序化赔偿估算），
 * 诊断成功后落库 diagnosis_reports，支持历史查看（本人或管理员）。
 */
@RestController
@RequestMapping("/api/diagnosis")
public class DiagnosisController {

    @Value("${rag.service.url}")
    private String ragServiceUrl;

    private final DiagnosisReportMapper reportMapper;
    private final ObjectMapper objectMapper;

    public DiagnosisController(DiagnosisReportMapper reportMapper, ObjectMapper objectMapper) {
        this.reportMapper = reportMapper;
        this.objectMapper = objectMapper;
    }

    @PostMapping
    public Map<String, Object> diagnose(@RequestBody Map<String, Object> body, HttpServletRequest request) {
        Object description = body == null ? null : body.get("description");
        if (description == null || String.valueOf(description).trim().length() < 5) {
            return Map.of("code", 400, "message", "请至少用 5 个字描述案情");
        }

        // 组装转发给 Python 的请求体（只透传已知字段）
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("description", String.valueOf(description).trim());
        payload.put("reason", String.valueOf(body.getOrDefault("reason", "被辞退")));
        try {
            payload.put("years", Double.valueOf(String.valueOf(body.getOrDefault("years", 1.0))));
            payload.put("monthly_wage", Double.valueOf(String.valueOf(body.getOrDefault("monthly_wage", 5000.0))));
        } catch (NumberFormatException e) {
            return Map.of("code", 400, "message", "工龄 / 月工资必须是数字");
        }
        payload.put("has_contract", Boolean.TRUE.equals(body.getOrDefault("has_contract", true)));

        try {
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(5000);
            factory.setReadTimeout(180000);  // LLM 诊断报告生成较慢

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(payload, headers);

            ResponseEntity<Map> resp = new RestTemplate(factory).postForEntity(
                    ragServiceUrl + "/api/diagnosis", entity, Map.class);
            Map<?, ?> data = resp.getBody();
            if (data == null) {
                return Map.of("code", 500, "message", "诊断生成失败：RAG 服务返回为空");
            }
            saveReport(payload, data, request);
            return Map.of("code", 200, "data", data);
        } catch (RestClientResponseException e) {
            return Map.of("code", 500, "message", extractDetail(e.getResponseBodyAsString(), "诊断生成失败"));
        } catch (Exception e) {
            return Map.of("code", 500, "message", "诊断生成失败：RAG 服务暂不可用");
        }
    }

    /** 诊断成功后落库（失败不影响主流程） */
    private void saveReport(Map<String, Object> payload, Map<?, ?> data, HttpServletRequest request) {
        try {
            DiagnosisReport report = new DiagnosisReport();
            report.setUserId((Long) request.getAttribute("userId"));
            report.setReason(String.valueOf(payload.get("reason")));
            report.setYears((Double) payload.get("years"));
            report.setMonthlyWage((Double) payload.get("monthly_wage"));
            report.setHasContract(Boolean.TRUE.equals(payload.get("has_contract")) ? 1 : 0);
            report.setDescription(String.valueOf(payload.get("description")));
            report.setSummary(data.get("summary") == null ? "" : String.valueOf(data.get("summary")));
            report.setIssues(toJson(data.get("issues")));
            report.setWarnings(toJson(data.get("warnings")));
            report.setNextSteps(toJson(data.get("next_steps")));
            report.setEstimation(toJson(data.get("estimation")));
            report.setSources(toJson(data.get("sources")));
            reportMapper.insert(report);
        } catch (Exception e) {
            // 历史记录保存失败不影响诊断结果返回
        }
    }

    /** 当前用户的历史报告列表（摘要级） */
    @GetMapping("/history")
    public Map<String, Object> history(HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        List<Map<String, Object>> items = new ArrayList<>();
        for (DiagnosisReport r : reportMapper.findByUser(userId)) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", r.getId());
            item.put("reason", r.getReason());
            item.put("years", r.getYears());
            item.put("monthlyWage", r.getMonthlyWage());
            item.put("hasContract", Integer.valueOf(1).equals(r.getHasContract()));
            item.put("description", r.getDescription());
            item.put("summary", r.getSummary());
            item.put("estimation", parseJson(r.getEstimation()));
            item.put("createdAt", r.getCreatedAt());
            items.add(item);
        }
        return Map.of("code", 200, "data", items);
    }

    /** 报告详情（本人或管理员可查），JSON 字段反序列化为对象 */
    @GetMapping("/history/{id}")
    public Map<String, Object> historyDetail(@PathVariable Long id, HttpServletRequest request) {
        DiagnosisReport r = reportMapper.findById(id);
        if (r == null) {
            return Map.of("code", 404, "message", "报告不存在或已删除");
        }
        Long userId = (Long) request.getAttribute("userId");
        if (!r.getUserId().equals(userId) && !"ADMIN".equals(request.getAttribute("role"))) {
            return Map.of("code", 403, "message", "无权查看该报告");
        }
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("id", r.getId());
        item.put("reason", r.getReason());
        item.put("years", r.getYears());
        item.put("monthlyWage", r.getMonthlyWage());
        item.put("hasContract", Integer.valueOf(1).equals(r.getHasContract()));
        item.put("description", r.getDescription());
        item.put("summary", r.getSummary());
        item.put("issues", parseJson(r.getIssues()));
        item.put("warnings", parseJson(r.getWarnings()));
        item.put("next_steps", parseJson(r.getNextSteps()));
        item.put("estimation", parseJson(r.getEstimation()));
        item.put("sources", parseJson(r.getSources()));
        item.put("createdAt", r.getCreatedAt());
        return Map.of("code", 200, "data", item);
    }

    private String toJson(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(value);
        } catch (Exception e) {
            return null;
        }
    }

    private Object parseJson(String json) {
        if (json == null || json.isBlank()) {
            return null;
        }
        try {
            return objectMapper.readValue(json, Object.class);
        } catch (Exception e) {
            return json;
        }
    }

    /** 从 Python 错误响应 {"detail": "..."} 中提取提示文案 */
    private String extractDetail(String body, String fallback) {
        if (body == null || body.isBlank()) {
            return fallback;
        }
        try {
            Object parsed = new com.fasterxml.jackson.databind.ObjectMapper().readValue(body, Object.class);
            if (parsed instanceof Map && ((Map<?, ?>) parsed).get("detail") != null) {
                return String.valueOf(((Map<?, ?>) parsed).get("detail"));
            }
        } catch (Exception ignored) {
        }
        return fallback;
    }
}
