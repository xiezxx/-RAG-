package com.labourlaw.mapper;

import com.labourlaw.entity.LoginLog;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface LoginLogMapper {
    @Insert("INSERT INTO login_logs (user_id, username, ip, success, message, created_at) VALUES (#{userId}, #{username}, #{ip}, #{success}, #{message}, NOW())")
    int insert(LoginLog log);

    @Select("SELECT id, user_id AS userId, username, ip, success, message, created_at AS createdAt FROM login_logs ORDER BY created_at DESC LIMIT #{limit}")
    List<LoginLog> findRecent(@Param("limit") int limit);
}
