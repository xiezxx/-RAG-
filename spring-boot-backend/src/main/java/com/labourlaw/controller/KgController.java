package com.labourlaw.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import javax.servlet.http.HttpServletRequest;
import java.util.*;

@RestController
@RequestMapping("/api/kg")
public class KgController {

    @Value("${rag.service.url}")
    private String ragServiceUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    /** 代理所有 KG 请求到 Python FastAPI */
    @GetMapping("/entities")
    public Map<String, Object> listEntities(@RequestParam(defaultValue = "LegalConcept") String entityType) {
        return proxyToPython("/api/kg/entities?entity_type=" + entityType);
    }

    @GetMapping("/all-entities")
    public Map<String, Object> allEntities() {
        return proxyToPython("/api/kg/all-entities");
    }

    @GetMapping("/stats")
    public Map<String, Object> stats() {
        return proxyToPython("/api/kg/stats");
    }

    @PostMapping("/entities")
    public Map<String, Object> createEntity(@RequestBody Map<String, Object> body, HttpServletRequest request) {
        if (!"ADMIN".equals(request.getAttribute("role"))) {
            return Map.of("code", 403, "message", "权限不足");
        }
        return proxyPostToPython("/api/kg/entities", body);
    }

    @DeleteMapping("/entities")
    public Map<String, Object> deleteEntity(@RequestParam String entityType, @RequestParam String name, HttpServletRequest request) {
        if (!"ADMIN".equals(request.getAttribute("role"))) {
            return Map.of("code", 403, "message", "权限不足");
        }
        try {
            String url = ragServiceUrl + "/api/kg/entities?entity_type=" +
                    java.net.URLEncoder.encode(entityType, java.nio.charset.StandardCharsets.UTF_8) +
                    "&name=" + java.net.URLEncoder.encode(name, java.nio.charset.StandardCharsets.UTF_8);
            restTemplate.delete(url);
            return Map.of("ok", true);
        } catch (Exception e) {
            return Map.of("error", "KG 服务暂不可用");
        }
    }

    private Map<String, Object> proxyToPython(String path) {
        try {
            String url = ragServiceUrl + path;
            return restTemplate.getForObject(url, Map.class);
        } catch (Exception e) {
            return Map.of("error", "KG 服务暂不可用: " + e.getMessage());
        }
    }

    private Map<String, Object> proxyPostToPython(String path, Map<String, Object> body) {
        try {
            String url = ragServiceUrl + path;
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
            return restTemplate.postForObject(url, entity, Map.class);
        } catch (Exception e) {
            return Map.of("error", "KG 服务暂不可用: " + e.getMessage());
        }
    }
}
