package com.labourlaw.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class LabourCase {
    private Long id;
    private String caseNumber;
    private String court;
    private String judgeDate;
    private String caseContent;
    private String issues;
    private String reasoning;
    private String judgment;
    private String legalBasis;
    private String keywords;
    private String category;
    private LocalDateTime createdAt;
}
