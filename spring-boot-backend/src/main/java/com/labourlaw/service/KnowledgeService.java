package com.labourlaw.service;

import com.labourlaw.entity.PopularizationArticle;
import com.labourlaw.mapper.PopularizationArticleMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import java.util.*;

@Service
public class KnowledgeService {

    @Autowired
    private PopularizationArticleMapper articleMapper;

    @Value("${rag.service.url}")
    private String ragServiceUrl;

    private final ObjectMapper objectMapper = new ObjectMapper();

    /** 带显式超时的 RestTemplate：文章生成 20-60s，默认无限超时不可接受 */
    private static RestTemplate buildRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(180000);
        return new RestTemplate(factory);
    }

    /** 文章列表（不含 content，含 hasContent 标记） */
    public List<Map<String, Object>> listArticles() {
        List<Map<String, Object>> result = new ArrayList<>();
        for (PopularizationArticle a : articleMapper.findAll()) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", a.getId());
            item.put("title", a.getTitle());
            item.put("category", a.getCategory());
            item.put("description", a.getDescription());
            item.put("generatedAt", a.getGeneratedAt() != null ? a.getGeneratedAt().toString() : null);
            item.put("hasContent", a.getContent() != null && !a.getContent().isBlank());
            result.add(item);
        }
        return result;
    }

    /** 文章详情（含 content 与解析后的 sources 数组） */
    public Map<String, Object> getArticle(Long id) {
        PopularizationArticle a = articleMapper.findById(id);
        if (a == null) {
            return null;
        }
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("id", a.getId());
        item.put("title", a.getTitle());
        item.put("category", a.getCategory());
        item.put("description", a.getDescription());
        item.put("content", a.getContent());
        item.put("sources", parseSources(a.getSources()));
        item.put("generatedAt", a.getGeneratedAt() != null ? a.getGeneratedAt().toString() : null);
        item.put("hasContent", a.getContent() != null && !a.getContent().isBlank());
        return item;
    }

    /** 调用 Python 生成文章并落库 */
    public Map<String, Object> generateArticle(Long id) {
        PopularizationArticle a = articleMapper.findById(id);
        if (a == null) {
            return null;
        }

        // 1. 调用 Python RAG 生成
        Map<String, Object> ragRequest = new HashMap<>();
        ragRequest.put("topic", a.getTitle());
        ragRequest.put("search_query", a.getSearchQuery() != null ? a.getSearchQuery() : "");

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(ragRequest, headers);

        ResponseEntity<Map> ragResponse;
        try {
            ragResponse = buildRestTemplate().postForEntity(
                    ragServiceUrl + "/api/knowledge/article", entity, Map.class);
        } catch (Exception e) {
            throw new RuntimeException("RAG 服务暂不可用");
        }

        Map<String, Object> body = ragResponse.getBody();
        if (body == null || body.get("content") == null) {
            throw new RuntimeException("RAG 服务返回为空");
        }
        String content = (String) body.get("content");
        Object rawSources = body.get("sources");

        // 2. sources 序列化落库
        String sourcesJson;
        try {
            sourcesJson = objectMapper.writeValueAsString(
                    rawSources instanceof List ? rawSources : List.of());
        } catch (Exception e) {
            sourcesJson = "[]";
        }
        articleMapper.updateGenerated(id, content, sourcesJson);

        return getArticle(id);
    }

    private List<Map<String, Object>> parseSources(String sourcesJson) {
        if (sourcesJson == null || sourcesJson.isBlank()) {
            return List.of();
        }
        try {
            Object parsed = objectMapper.readValue(sourcesJson, Object.class);
            if (parsed instanceof List) {
                return (List<Map<String, Object>>) (List) parsed;
            }
        } catch (Exception ignored) {
        }
        return List.of();
    }

    // ── 互动式普法（情景剧/海报/短片）通用代理 ──

    /** POST 转发到 Python /api/knowledge/**，返回 JSON 对象（4xx/5xx 会抛 RestClientResponseException） */
    public Map<String, Object> proxyPost(String path, Map<String, Object> body) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
        ResponseEntity<Map> resp = buildRestTemplate().postForEntity(ragServiceUrl + path, entity, Map.class);
        return resp.getBody();
    }

    /** GET 转发到 Python /api/knowledge/**，返回 JSON 数组（必须按 List 反序列化，不能用 Map.class） */
    public List<?> proxyGetList(String path) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(30000);
        List<?> list = new RestTemplate(factory).getForObject(ragServiceUrl + path, List.class);
        return list != null ? list : List.of();
    }

    /** GET 转发到 Python /api/knowledge/**，返回 JSON 对象 */
    public Map<String, Object> proxyGetMap(String path) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(60000);
        Map<String, Object> map = new RestTemplate(factory).getForObject(ragServiceUrl + path, Map.class);
        return map != null ? map : Map.of();
    }
}
