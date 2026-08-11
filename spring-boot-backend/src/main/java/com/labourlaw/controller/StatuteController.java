package com.labourlaw.controller;

import com.labourlaw.entity.Statute;
import com.labourlaw.mapper.StatuteMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import javax.servlet.http.HttpServletRequest;
import java.io.*;
import java.nio.file.*;
import java.util.*;

@RestController
@RequestMapping("/api/statutes")
public class StatuteController {

    @Autowired
    private StatuteMapper statuteMapper;

    // 法律文档存储目录
    private static final String UPLOAD_DIR = System.getProperty("user.dir") + "/src/data/raw/statutes/";

    /** 法条列表：缓存 24h（Redis 不可用时自动降级查库） */
    @GetMapping
    @Cacheable(value = "statutes", key = "'list'")
    public Map<String, Object> list() {
        List<Statute> statutes = statuteMapper.findAll();
        List<Map<String, Object>> result = new ArrayList<>();
        for (Statute s : statutes) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id", s.getId());
            row.put("name", s.getName());
            row.put("category", s.getCategory() != null ? s.getCategory() : "法律");
            row.put("articleCount", s.getArticleCount());
            row.put("publishDate", s.getPublishDate());
            row.put("effectiveDate", s.getEffectiveDate());
            row.put("status", s.getStatus() != null ? s.getStatus() : "现行有效");
            row.put("documentNumber", s.getDocumentNumber());
            row.put("issuingAuthority", s.getIssuingAuthority());
            row.put("applicableRegion", s.getApplicableRegion());
            row.put("applicableSubject", s.getApplicableSubject());
            row.put("createdAt", s.getCreatedAt());
            result.add(row);
        }
        return Map.of("code", 200, "data", result);
    }

    @PostMapping
    @CacheEvict(value = "statutes", key = "'list'")
    public Map<String, Object> add(@RequestBody Map<String, Object> body, HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");

        Statute statute = new Statute();
        statute.setName((String) body.getOrDefault("name", ""));
        statute.setCategory((String) body.getOrDefault("category", "法律"));
        statute.setArticleCount((Integer) body.getOrDefault("articleCount", 0));
        statute.setPublishDate((String) body.getOrDefault("publishDate", ""));
        statute.setEffectiveDate((String) body.getOrDefault("effectiveDate", ""));
        statute.setStatus((String) body.getOrDefault("status", "现行有效"));
        statute.setDocumentNumber((String) body.getOrDefault("documentNumber", ""));
        statute.setIssuingAuthority((String) body.getOrDefault("issuingAuthority", ""));
        statute.setApplicableRegion((String) body.getOrDefault("applicableRegion", ""));
        statute.setApplicableSubject((String) body.getOrDefault("applicableSubject", ""));
        statuteMapper.insert(statute);
        body.put("id", statute.getId());
        return Map.of("code", 200, "data", body, "message", "添加成功");
    }

    @PutMapping("/{id}")
    @CacheEvict(value = "statutes", key = "'list'")
    public Map<String, Object> update(@PathVariable Long id, @RequestBody Map<String, Object> body, HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");

        Statute statute = new Statute();
        statute.setId(id);
        statute.setName((String) body.getOrDefault("name", ""));
        statute.setCategory((String) body.getOrDefault("category", "法律"));
        statute.setArticleCount((Integer) body.getOrDefault("articleCount", 0));
        statute.setPublishDate((String) body.getOrDefault("publishDate", ""));
        statute.setEffectiveDate((String) body.getOrDefault("effectiveDate", ""));
        statute.setStatus((String) body.getOrDefault("status", "现行有效"));
        statute.setDocumentNumber((String) body.getOrDefault("documentNumber", ""));
        statute.setIssuingAuthority((String) body.getOrDefault("issuingAuthority", ""));
        statute.setApplicableRegion((String) body.getOrDefault("applicableRegion", ""));
        statute.setApplicableSubject((String) body.getOrDefault("applicableSubject", ""));
        statuteMapper.update(statute);
        return Map.of("code", 200, "message", "更新成功");
    }

    @DeleteMapping("/{id}")
    @CacheEvict(value = "statutes", key = "'list'")
    public Map<String, Object> delete(@PathVariable Long id, HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");

        statuteMapper.deleteById(id);
        return Map.of("code", 200, "message", "删除成功");
    }

    /** 上传法律文档（.txt / .docx），自动解析入库 */
    @PostMapping("/upload")
    @CacheEvict(value = "statutes", key = "'list'")
    public Map<String, Object> upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "name", defaultValue = "") String name,
            @RequestParam(value = "category", defaultValue = "法律") String category,
            @RequestParam(value = "publishDate", defaultValue = "") String publishDate,
            @RequestParam(value = "effectiveDate", defaultValue = "") String effectiveDate,
            @RequestParam(value = "status", defaultValue = "现行有效") String status,
            @RequestParam(value = "documentNumber", defaultValue = "") String documentNumber,
            @RequestParam(value = "issuingAuthority", defaultValue = "") String issuingAuthority,
            @RequestParam(value = "applicableRegion", defaultValue = "") String applicableRegion,
            @RequestParam(value = "applicableSubject", defaultValue = "") String applicableSubject,
            HttpServletRequest request) {

        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");

        if (file.isEmpty()) return Map.of("code", 400, "message", "文件不能为空");

        String originalName = file.getOriginalFilename();
        if (originalName == null || (!originalName.endsWith(".txt") && !originalName.endsWith(".docx"))) {
            return Map.of("code", 400, "message", "仅支持 .txt 或 .docx 格式");
        }

        try {
            // 确保上传目录存在
            Files.createDirectories(Paths.get(UPLOAD_DIR));

            // 保存文件
            String fileName = (name.isEmpty() ? originalName.replaceFirst("\\.[^.]+$", "") : name)
                    + "_" + effectiveDate.replace("-", "")
                    + originalName.substring(originalName.lastIndexOf('.'));
            Path filePath = Paths.get(UPLOAD_DIR, fileName);
            file.transferTo(filePath.toFile());

            // 统计条文数（按空行或"第X条"切分估算）
            int articleCount = estimateArticleCount(filePath);

            // 写入 MySQL
            Statute statute = new Statute();
            statute.setName(name.isEmpty() ? originalName.replaceFirst("\\.[^.]+$", "") : name);
            statute.setCategory(category);
            statute.setArticleCount(articleCount);
            statute.setPublishDate(publishDate);
            statute.setEffectiveDate(effectiveDate);
            statute.setStatus(status);
            statute.setDocumentNumber(documentNumber);
            statute.setIssuingAuthority(issuingAuthority);
            statute.setApplicableRegion(applicableRegion);
            statute.setApplicableSubject(applicableSubject);
            statuteMapper.insert(statute);

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("id", statute.getId());
            result.put("fileName", fileName);
            result.put("articleCount", articleCount);
            result.put("filePath", filePath.toString());
            return Map.of("code", 200, "data", result, "message", "上传成功，已入库 " + articleCount + " 条");
        } catch (IOException e) {
            return Map.of("code", 500, "message", "文件保存失败: " + e.getMessage());
        }
    }

    /** 估算上传文档中的条文数量 */
    private int estimateArticleCount(Path filePath) throws IOException {
        String content = Files.readString(filePath);
        // 匹配 "第X条" 模式
        int count = 0;
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("第[一二三四五六七八九十百千\\d]+条").matcher(content);
        while (m.find()) count++;
        // 如果没匹配到，按空行切分估算段落数
        if (count == 0) {
            count = content.split("\\n\\s*\\n").length;
        }
        return Math.max(count, 1);
    }
}
