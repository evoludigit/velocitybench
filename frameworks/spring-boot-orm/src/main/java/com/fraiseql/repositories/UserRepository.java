package com.fraiseql.repositories;

import com.fraiseql.entities.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface UserRepository extends JpaRepository<User, Integer> {

    @Query(value = "SELECT * FROM benchmark.tb_user WHERE id = :id", nativeQuery = true)
    User findByUuid(@Param("id") String id);

    @Query(value = "SELECT * FROM benchmark.tb_user ORDER BY created_at DESC LIMIT :limit", nativeQuery = true)
    List<User> findUsersWithLimit(@Param("limit") int limit);
}