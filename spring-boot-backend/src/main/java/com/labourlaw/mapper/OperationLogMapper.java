package com.labourlaw.mapper;

import com.labourlaw.entity.OperationLog;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface OperationLogMapper {
    @Insert("INSERT INTO operation_logs (user_id, username, action, target, ip, created_at) VALUES (#{userId}, #{username}, #{action}, #{target}, #{ip}, NOW())")
    int insert(OperationLog log);

    @Select("SELECT id, user_id AS userId, username, action, target, ip, created_at AS createdAt FROM operation_logs ORDER BY created_at DESC LIMIT #{limit}")
    List<OperationLog> findRecent(@Param("limit") int limit);
}
