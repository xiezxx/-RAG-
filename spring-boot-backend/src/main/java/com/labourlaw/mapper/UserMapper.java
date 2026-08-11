package com.labourlaw.mapper;

import com.labourlaw.entity.*;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface UserMapper {
    @Select("SELECT * FROM users WHERE username = #{username}")
    User findByUsername(String username);

    @Insert("INSERT INTO users (username, password, name, phone, role, status, created_at) VALUES (#{username}, #{password}, #{name}, #{phone}, 'USER', '启用', NOW())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(User user);

    @Select("SELECT * FROM users WHERE id = #{id}")
    User findById(Long id);

    @Update("UPDATE users SET password = #{password} WHERE id = #{id}")
    int updatePassword(@Param("id") Long id, @Param("password") String password);

    @Select("SELECT * FROM users ORDER BY id")
    List<User> findAll();

    @Update("UPDATE users SET role = #{role}, status = #{status} WHERE id = #{id}")
    int updateRoleStatus(@Param("id") Long id, @Param("role") String role, @Param("status") String status);

    @Delete("DELETE FROM users WHERE id = #{id}")
    int deleteById(Long id);

    @Select("SELECT COUNT(*) FROM users")
    int count();
}
