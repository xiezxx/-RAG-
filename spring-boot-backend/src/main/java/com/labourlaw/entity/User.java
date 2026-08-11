package com.labourlaw.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class User {
    private Long id;
    private String username;
    private String password;
    private String name;         // 姓名
    private String phone;        // 联系方式
    private String role;         // ADMIN / USER
    private String status;       // 启用 / 停用
    private LocalDateTime createdAt;
}
