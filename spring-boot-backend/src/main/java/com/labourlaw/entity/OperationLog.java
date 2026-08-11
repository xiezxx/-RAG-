package com.labourlaw.entity;

import lombok.Data;

@Data
public class OperationLog {
    private Long id;
    private Long userId;
    private String username;
    private String action;
    private String target;
    private String ip;
    private String createdAt;
}
