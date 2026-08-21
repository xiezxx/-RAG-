package com.labourlaw.service;

import com.labourlaw.config.JwtUtil;
import com.labourlaw.dto.*;
import com.labourlaw.entity.*;
import com.labourlaw.mapper.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private PasswordEncoder passwordEncoder;

    /**
     * 登录：验证密码 → 签发 JWT
     */
    public LoginResponse login(LoginRequest request) {
        User user = userMapper.findByUsername(request.getUsername());
        if (user == null) {
            throw new RuntimeException("用户名或密码错误");
        }
        if ("停用".equals(user.getStatus())) {
            throw new RuntimeException("用户已停用");
        }

        // BCrypt 密码校验；兼容旧明文密码（自动升级为 BCrypt）
        String storedPassword = user.getPassword();
        boolean passwordOk = false;

        if (storedPassword != null && storedPassword.startsWith("$2")) {
            // BCrypt 哈希
            passwordOk = passwordEncoder.matches(request.getPassword(), storedPassword);
        } else {
            // 旧明文密码 → 比对后自动升级
            if (request.getPassword().equals(storedPassword)) {
                passwordOk = true;
                // 自动升级密码为 BCrypt
                userMapper.updatePassword(user.getId(), passwordEncoder.encode(request.getPassword()));
            }
        }

        if (!passwordOk) {
            throw new RuntimeException("用户名或密码错误");
        }

        // 使用 JwtUtil 签发 token
        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), user.getRole());

        LoginResponse resp = new LoginResponse();
        resp.setToken(token);
        resp.setUsername(user.getUsername());
        resp.setRole(user.getRole());
        return resp;
    }

    /**
     * 注册：BCrypt 哈希密码后存入数据库
     */
    public User register(LoginRequest request) {
        // 基本校验
        if (request.getUsername() == null || request.getUsername().trim().isEmpty()) {
            throw new RuntimeException("用户名不能为空");
        }
        if (request.getPassword() == null || request.getPassword().trim().isEmpty()) {
            throw new RuntimeException("密码不能为空");
        }
        if (request.getPassword().length() < 6) {
            throw new RuntimeException("密码长度不能少于6位");
        }

        User existing = userMapper.findByUsername(request.getUsername());
        if (existing != null) {
            throw new RuntimeException("用户名已存在");
        }

        User user = new User();
        user.setUsername(request.getUsername().trim());
        user.setName(request.getName() != null ? request.getName().trim() : request.getUsername().trim());
        user.setPhone(request.getPhone() != null ? request.getPhone().trim() : "");

        // BCrypt 哈希密码
        user.setPassword(passwordEncoder.encode(request.getPassword()));

        userMapper.insert(user);
        return user;
    }

    /**
     * 管理员新增用户（可指定角色/状态）
     */
    public User createUser(String username, String password, String name, String phone, String role, String status) {
        if (username == null || username.trim().isEmpty()) {
            throw new RuntimeException("用户名不能为空");
        }
        if (password == null || password.isEmpty()) {
            throw new RuntimeException("密码不能为空");
        }
        if (password.length() < 6) {
            throw new RuntimeException("密码长度不能少于6位");
        }
        if (userMapper.findByUsername(username.trim()) != null) {
            throw new RuntimeException("用户名已存在");
        }
        if (!"ADMIN".equals(role) && !"RESEARCHER".equals(role) && !"USER".equals(role)) {
            throw new RuntimeException("角色不合法");
        }

        User user = new User();
        user.setUsername(username.trim());
        user.setPassword(passwordEncoder.encode(password));
        user.setName(name != null && !name.trim().isEmpty() ? name.trim() : username.trim());
        user.setPhone(phone != null ? phone.trim() : "");
        user.setRole(role);
        user.setStatus("停用".equals(status) ? "停用" : "启用");
        userMapper.insertFull(user);
        return user;
    }
}
