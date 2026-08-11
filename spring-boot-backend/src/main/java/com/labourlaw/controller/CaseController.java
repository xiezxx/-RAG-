package com.labourlaw.controller;

import com.labourlaw.entity.*;
import com.labourlaw.service.CaseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import javax.servlet.http.HttpServletRequest;
import java.util.*;

@RestController
@RequestMapping("/api/cases")
public class CaseController {

    @Autowired
    private CaseService caseService;

    @GetMapping
    public Map<String, Object> list(@RequestParam(required = false) String category,
                                     @RequestParam(required = false) String keyword) {
        List<LabourCase> cases;
        if (keyword != null && !keyword.isEmpty()) {
            cases = caseService.search(keyword);
        } else if (category != null && !category.isEmpty()) {
            cases = caseService.findByCategory(category);
        } else {
            cases = caseService.findAll();
        }
        return Map.of("code", 200, "data", cases, "total", cases.size());
    }

    @GetMapping("/{id}")
    public Map<String, Object> detail(@PathVariable Long id) {
        LabourCase c = caseService.findById(id);
        return c != null
            ? Map.of("code", 200, "data", c)
            : Map.of("code", 404, "message", "案例不存在");
    }

    @PostMapping
    public Map<String, Object> add(@RequestBody LabourCase labourCase,
                                    HttpServletRequest request) {
        // 仅 ADMIN 可添加案例
        String role = (String) request.getAttribute("role");
        if (!"ADMIN".equals(role)) {
            return Map.of("code", 403, "message", "权限不足，仅管理员可添加案例");
        }
        caseService.add(labourCase);
        return Map.of("code", 200, "data", labourCase, "message", "添加成功");
    }

    @GetMapping("/stats")
    public Map<String, Object> stats() {
        return Map.of("code", 200, "data", Map.of("total", caseService.count()));
    }
}
