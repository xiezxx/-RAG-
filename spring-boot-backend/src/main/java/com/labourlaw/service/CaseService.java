package com.labourlaw.service;

import com.labourlaw.entity.*;
import com.labourlaw.mapper.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class CaseService {

    @Autowired
    private CaseMapper caseMapper;

    public List<LabourCase> findAll() {
        return caseMapper.findAll();
    }

    public LabourCase findById(Long id) {
        return caseMapper.findById(id);
    }

    public List<LabourCase> findByCategory(String category) {
        return caseMapper.findByCategory(category);
    }

    /** 热点查询结果缓存 1h（相同关键词命中 Redis，避免重复查库） */
    @Cacheable(value = "hotQuestions", key = "#keyword")
    public List<LabourCase> search(String keyword) {
        return caseMapper.search(keyword);
    }

    public LabourCase add(LabourCase labourCase) {
        caseMapper.insert(labourCase);
        return labourCase;
    }

    public int count() {
        return caseMapper.count();
    }
}
