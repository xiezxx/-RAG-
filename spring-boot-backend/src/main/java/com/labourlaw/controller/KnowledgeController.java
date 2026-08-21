package com.labourlaw.controller;

import com.labourlaw.service.KnowledgeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;
import java.util.*;

@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    @Autowired
    private KnowledgeService knowledgeService;

    @Value("${rag.service.url}")
    private String ragServiceUrl;

    /** 科普专题文章列表（不含正文） */
    @GetMapping("/articles")
    public Map<String, Object> listArticles() {
        return Map.of("code", 200, "data", knowledgeService.listArticles());
    }

    /** 文章详情（含正文与来源） */
    @GetMapping("/articles/{id}")
    public Map<String, Object> getArticle(@PathVariable Long id) {
        Map<String, Object> article = knowledgeService.getArticle(id);
        if (article == null) {
            return Map.of("code", 404, "message", "文章不存在");
        }
        return Map.of("code", 200, "data", article);
    }

    /** 生成（或重新生成）文章，由 Python RAG + LLM 生成后缓存 */
    @PostMapping("/articles/{id}/generate")
    public Map<String, Object> generateArticle(@PathVariable Long id) {
        Map<String, Object> article;
        try {
            article = knowledgeService.generateArticle(id);
        } catch (Exception e) {
            return Map.of("code", 500, "message", "生成失败：" + e.getMessage() + "，请稍后重试");
        }
        if (article == null) {
            return Map.of("code", 404, "message", "文章不存在");
        }
        return Map.of("code", 200, "data", article, "message", "生成成功");
    }

    /** 名词卡片：代理 Python /api/knowledge/terms（注意返回 JSON 数组，须按 List 反序列化） */
    @GetMapping("/terms")
    public Map<String, Object> terms() {
        try {
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(5000);
            factory.setReadTimeout(30000);
            List<?> list = new RestTemplate(factory).getForObject(
                    ragServiceUrl + "/api/knowledge/terms", List.class);
            return Map.of("code", 200, "data", list != null ? list : List.of());
        } catch (Exception e) {
            return Map.of("code", 500, "message", "术语数据暂不可用");
        }
    }

    // ── 互动式普法：情景剧 / 海报 / 短片 ──

    /** 情景剧剧本库 */
    @GetMapping("/stories")
    public Map<String, Object> stories() {
        try {
            return Map.of("code", 200, "data", knowledgeService.proxyGetList("/api/knowledge/stories"));
        } catch (Exception e) {
            return Map.of("code", 500, "message", "剧本数据暂不可用");
        }
    }

    /** 情景剧开场（第 1 幕） */
    @PostMapping("/scene/start")
    public Map<String, Object> sceneStart(@RequestBody Map<String, Object> body) {
        return proxyPost("/api/knowledge/scene/start", body, "开场生成失败");
    }

    /** 情景剧判定 + 下一幕 / 结局 */
    @PostMapping("/scene/next")
    public Map<String, Object> sceneNext(@RequestBody Map<String, Object> body) {
        return proxyPost("/api/knowledge/scene/next", body, "剧情推进失败");
    }

    /** 普法海报文案生成 */
    @PostMapping("/poster")
    public Map<String, Object> poster(@RequestBody Map<String, Object> body) {
        return proxyPost("/api/knowledge/poster", body, "海报生成失败");
    }

    /** 普法短片分镜 + 配音生成 */
    @PostMapping("/video")
    public Map<String, Object> video(@RequestBody Map<String, Object> body) {
        return proxyPost("/api/knowledge/video", body, "短片生成失败");
    }

    // ── 预置内容（已生成的海报/短片，秒开不等待 LLM） ──

    /** 已生成的普法海报（全量） */
    @GetMapping("/poster/presets")
    public Map<String, Object> posterPresets() {
        try {
            return Map.of("code", 200, "data", knowledgeService.proxyGetList("/api/knowledge/poster/presets"));
        } catch (Exception e) {
            return Map.of("code", 500, "message", "预置海报暂不可用");
        }
    }

    /** 已生成的普法短片列表（轻量，不含配音） */
    @GetMapping("/video/presets")
    public Map<String, Object> videoPresets() {
        try {
            return Map.of("code", 200, "data", knowledgeService.proxyGetList("/api/knowledge/video/presets"));
        } catch (Exception e) {
            return Map.of("code", 500, "message", "预置短片暂不可用");
        }
    }

    /** 单部预置短片全文（含配音 dataURI，体量大按需拉取） */
    @GetMapping("/video/presets/{id}")
    public Map<String, Object> videoPresetDetail(@PathVariable int id) {
        try {
            Map<String, Object> data = knowledgeService.proxyGetMap("/api/knowledge/video/presets/" + id);
            if (data.isEmpty()) {
                return Map.of("code", 404, "message", "该预置短片不存在");
            }
            return Map.of("code", 200, "data", data);
        } catch (RestClientResponseException e) {
            return Map.of("code", 404, "message", extractDetail(e.getResponseBodyAsString(), "该预置短片不存在"));
        } catch (Exception e) {
            return Map.of("code", 500, "message", "预置短片暂不可用");
        }
    }

    /** 统一 POST 代理：成功包 {code:200,data}；转发 Python 的 4xx 详情；异常兜底 */
    private Map<String, Object> proxyPost(String path, Map<String, Object> body, String failMessage) {
        try {
            Map<String, Object> data = knowledgeService.proxyPost(path, body);
            if (data == null) {
                return Map.of("code", 500, "message", failMessage + "：RAG 服务返回为空");
            }
            return Map.of("code", 200, "data", data);
        } catch (RestClientResponseException e) {
            // Python 端 4xx（如“剧本不存在”）——把 detail 原样透传给前端
            return Map.of("code", 500, "message", extractDetail(e.getResponseBodyAsString(), failMessage));
        } catch (Exception e) {
            return Map.of("code", 500, "message", failMessage + "：RAG 服务暂不可用");
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
