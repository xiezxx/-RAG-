package com.labourlaw.mapper;

import com.labourlaw.entity.*;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface CaseMapper {
    @Select("SELECT * FROM labour_cases ORDER BY created_at DESC")
    List<LabourCase> findAll();

    @Select("SELECT * FROM labour_cases WHERE id = #{id}")
    LabourCase findById(Long id);

    @Select("SELECT * FROM labour_cases WHERE category = #{category} ORDER BY created_at DESC")
    List<LabourCase> findByCategory(String category);

    @Select("SELECT * FROM labour_cases WHERE keywords LIKE CONCAT('%', #{keyword}, '%') " +
            "OR case_number LIKE CONCAT('%', #{keyword}, '%') ORDER BY created_at DESC")
    List<LabourCase> search(String keyword);

    @Insert("INSERT INTO labour_cases (case_number, court, judge_date, case_content, issues, " +
            "reasoning, judgment, legal_basis, keywords, category, created_at) " +
            "VALUES (#{caseNumber}, #{court}, #{judgeDate}, #{caseContent}, #{issues}, " +
            "#{reasoning}, #{judgment}, #{legalBasis}, #{keywords}, #{category}, NOW())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(LabourCase labourCase);

    @Select("SELECT count(*) FROM labour_cases")
    int count();
}
