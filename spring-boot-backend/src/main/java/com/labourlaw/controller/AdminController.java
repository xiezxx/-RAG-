package com.labourlaw.controller;

import com.labourlaw.entity.*;
import com.labourlaw.mapper.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import javax.servlet.http.HttpServletRequest;
import java.util.*;

@RestController
@RequestMapping("/api/admin")
public class AdminController {

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private OperationLogMapper logMapper;

    @Autowired
    private ChatHistoryMapper chatHistoryMapper;

    @Autowired
    private StatuteMapper statuteMapper;

    /** 列出所有用户 */
    @GetMapping("/users")
    public Map<String, Object> listUsers(HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");

        List<User> users = userMapper.findAll();
        List<Map<String, Object>> result = new ArrayList<>();
        for (User u : users) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id", u.getId());
            row.put("username", u.getUsername());
            row.put("name", u.getName());
            row.put("phone", u.getPhone());
            row.put("role", u.getRole());
            row.put("status", u.getStatus());
            row.put("createdAt", u.getCreatedAt());
            result.add(row);
        }
        return Map.of("code", 200, "data", result);
    }

    /** 更新用户角色/状态 */
    @PutMapping("/users/{id}")
    public Map<String, Object> updateUser(@PathVariable Long id, @RequestBody Map<String, String> body, HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");

        String newRole = body.getOrDefault("role", "USER");
        String newStatus = body.getOrDefault("status", "启用");
        userMapper.updateRoleStatus(id, newRole, newStatus);
        logOperation(request, "更新用户", "用户ID=" + id);
        return Map.of("code", 200, "message", "更新成功");
    }

    /** 删除用户 */
    @DeleteMapping("/users/{id}")
    public Map<String, Object> deleteUser(@PathVariable Long id, HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");

        userMapper.deleteById(id);
        logOperation(request, "删除用户", "用户ID=" + id);
        return Map.of("code", 200, "message", "删除成功");
    }

    /** 操作日志列表 */
    @GetMapping("/logs")
    public Map<String, Object> logs(@RequestParam(defaultValue = "50") int limit, HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");
        return Map.of("code", 200, "data", logMapper.findRecent(limit));
    }

    /** 系统统计 */
    @GetMapping("/stats")
    public Map<String, Object> stats(HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) return Map.of("code", 403, "message", "权限不足");

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("users", userMapper.count());
        stats.put("chats", chatHistoryMapper.count());
        stats.put("cases", chatHistoryMapper.countCases());
        stats.put("statutes", statuteMapper.count());
        return Map.of("code", 200, "data", stats);
    }

    /** 记录操作日志 */
    private void logOperation(HttpServletRequest request, String action, String target) {
        try {
            OperationLog log = new OperationLog();
            log.setUserId((Long) request.getAttribute("userId"));
            log.setUsername((String) request.getAttribute("username"));
            log.setAction(action);
            log.setTarget(target);
            log.setIp(request.getRemoteAddr());
            logMapper.insert(log);
        } catch (Exception ignored) {}
    }
}
