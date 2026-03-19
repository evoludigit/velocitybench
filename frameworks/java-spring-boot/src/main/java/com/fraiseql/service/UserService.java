package com.fraiseql.service;

import com.fraiseql.dto.UserDTO;
import com.fraiseql.models.User;
import com.fraiseql.repository.UserRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public Optional<UserDTO> getUserById(String uuid) {
        return userRepository.findByUuid(uuid)
                .map(this::toDTO);
    }

    public List<UserDTO> getAllUsers(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        List<User> users = userRepository.findAllByOrderByUsername(pageable);
        return users.stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    @Transactional
    public Optional<UserDTO> updateBio(String uuid, String bio) {
        return userRepository.findByUuid(uuid)
                .map(user -> {
                    user.setBio(bio);
                    user.setUpdatedAt(LocalDateTime.now());
                    return toDTO(userRepository.save(user));
                });
    }

    private UserDTO toDTO(User user) {
        if (user == null) {
            return null;
        }
        UserDTO dto = new UserDTO();
        dto.setId(user.getId());
        dto.setUsername(user.getUsername());
        dto.setFullName(user.getFullName());
        dto.setBio(user.getBio());
        return dto;
    }
}
