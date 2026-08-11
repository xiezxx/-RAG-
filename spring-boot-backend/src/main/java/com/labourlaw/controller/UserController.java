package com.labourlaw.controller;

import com.labourlaw.dto.*;
import com.labourlaw.entity.User;
import com.labourlaw.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class UserController {

    @Autowired
    private UserService userService;

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody LoginRequest request) {
        try {
            LoginResponse resp = userService.login(request);
            return Map.of("code", 200, "data", resp, "message", "登录成功");
        } catch (Exception e) {
            return Map.of("code", 401, "message", e.getMessage());
        }
    }

    @PostMapping("/register")
    public Map<String, Object> register(@RequestBody LoginRequest request) {
        try {
            User user = userService.register(request);
            user.setPassword(null);
            return Map.of("code", 200, "data", user, "message", "注册成功");
        } catch (Exception e) {
            return Map.of("code", 400, "message", e.getMessage());
        }
    }
}
