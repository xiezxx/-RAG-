package com.labourlaw.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import java.util.List;
import java.util.Map;

/**
 * 法条版本对照代理（模块5 时效感知·法条版本管理）
 * 转发 Python /api/version/* —— 提供新旧版本条文对比数据
 */
@RestController
@RequestMapping("/api/version")
public class VersionCompareController {

    @Value("${rag.service.url}")
    private String ragServiceUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    /** 列出存在新旧版本的法律及版本信息 */
    @GetMapping("/laws")
    public Map<String, Object> laws() {
        try {
            List<?> data = restTemplate.getForObject(ragServiceUrl + "/api/version/laws", List.class);
            return Map.of("code", 200, "data", data == null ? List.of() : data);
        } catch (RestClientException e) {
            return Map.of("code", 500, "message", "版本数据暂不可用");
        }
    }

    /** 对比某部法律某条文的新旧版本内容 */
    @GetMapping("/compare")
    public Map<String, Object> compare(@RequestParam String law, @RequestParam String article) {
        try {
            // 中文参数显式 UTF-8 编码，并直接传 URI 而非 String，
            // 避免 RestTemplate 的 URI 模板处理器二次编码（% → %25）
            String encoded = ragServiceUrl + "/api/version/compare?law="
                    + java.net.URLEncoder.encode(law, java.nio.charset.StandardCharsets.UTF_8)
                    + "&article=" + java.net.URLEncoder.encode(article, java.nio.charset.StandardCharsets.UTF_8);
            Map<?, ?> result = restTemplate.getForObject(new java.net.URI(encoded), Map.class);
            if (result == null || !Boolean.TRUE.equals(result.get("found"))) {
                String msg = result != null && result.get("message") != null
                        ? result.get("message").toString() : "该法律或条文暂无多版本修订数据";
                return Map.of("code", 404, "message", msg);
            }
            return Map.of("code", 200, "data", result);
        } catch (RestClientException | java.net.URISyntaxException e) {
            return Map.of("code", 500, "message", "版本对比服务暂不可用，请稍后重试");
        }
    }
}
