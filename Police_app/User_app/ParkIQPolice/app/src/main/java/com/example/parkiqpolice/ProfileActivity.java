package com.example.parkiqpolice;

import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.material.textfield.TextInputEditText;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.SetOptions;

import java.util.HashMap;
import java.util.Map;

public class ProfileActivity extends BaseNavigationActivity {

    TextView txtName;
    TextView txtEmail;
    TextInputEditText edtName;
    TextInputEditText edtAge;
    TextInputEditText edtGender;
    TextInputEditText edtBadge;
    TextInputEditText edtDepartment;
    TextInputEditText edtPhone;
    Button btnSave;
    Button btnLogout;

    FirebaseFirestore db;
    FirebaseUser currentUser;
    LoadingDialog loadingDialog;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        txtName = findViewById(R.id.txtName);
        txtEmail = findViewById(R.id.txtEmail);
        edtName = findViewById(R.id.edtName);
        edtAge = findViewById(R.id.edtAge);
        edtGender = findViewById(R.id.edtGender);
        edtBadge = findViewById(R.id.edtBadge);
        edtDepartment = findViewById(R.id.edtDepartment);
        edtPhone = findViewById(R.id.edtPhone);
        btnSave = findViewById(R.id.btnSave);
        btnLogout = findViewById(R.id.btnLogout);

        db = FirebaseFirestore.getInstance();
        currentUser = FirebaseAuth.getInstance().getCurrentUser();
        loadingDialog = new LoadingDialog(this);

        if (currentUser == null) {
            redirectToLogin();
            return;
        }

        loadProfile();

        btnSave.setOnClickListener(v -> saveProfile());
        btnLogout.setOnClickListener(v -> {
            FirebaseAuth.getInstance().signOut();
            redirectToLogin();
        });
    }

    @Override
    protected int getContentLayoutId() {
        return R.layout.activity_profile;
    }

    @Override
    protected int getSelectedMenuItemId() {
        return R.id.nav_profile;
    }

    private void loadProfile() {
        loadingDialog.show();
        if (currentUser == null) {
            loadingDialog.hide();
            return;
        }

        String uid = currentUser.getUid();
        db.collection("users")
                .document(uid)
                .get()
                .addOnSuccessListener(document -> {
                    populateFields(document);
                    loadingDialog.hide();
                })
                .addOnFailureListener(e -> {
                    loadingDialog.hide();
                    Toast.makeText(
                            this,
                            R.string.profile_error_load,
                            Toast.LENGTH_SHORT
                    ).show();
                });
    }

    private void populateFields(DocumentSnapshot document) {
        if (document.exists()) {
            edtName.setText(document.getString("name"));
            edtAge.setText(document.getString("age"));
            edtGender.setText(document.getString("gender"));
            edtBadge.setText(document.getString("badgeNumber"));
            edtDepartment.setText(document.getString("department"));
            edtPhone.setText(document.getString("phone"));
        }

        String currentName = currentUser.getDisplayName();
        String currentEmail = currentUser.getEmail();

        if (currentName != null && !currentName.isEmpty()) {
            txtName.setText(currentName);
            if (edtName.getText() == null || edtName.getText().toString().trim().isEmpty()) {
                edtName.setText(currentName);
            }
        }

        if (currentEmail != null && !currentEmail.isEmpty()) {
            txtEmail.setText(currentEmail);
        }
    }

    private void saveProfile() {
        if (currentUser == null) {
            redirectToLogin();
            return;
        }

        String name = edtName.getText() != null ? edtName.getText().toString().trim() : "";
        String age = edtAge.getText() != null ? edtAge.getText().toString().trim() : "";
        String gender = edtGender.getText() != null ? edtGender.getText().toString().trim() : "";
        String badge = edtBadge.getText() != null ? edtBadge.getText().toString().trim() : "";
        String department = edtDepartment.getText() != null ? edtDepartment.getText().toString().trim() : "";
        String phone = edtPhone.getText() != null ? edtPhone.getText().toString().trim() : "";

        Map<String, Object> profile = new HashMap<>();
        profile.put("name", name);
        profile.put("age", age);
        profile.put("gender", gender);
        profile.put("badgeNumber", badge);
        profile.put("department", department);
        profile.put("phone", phone);
        profile.put("email", currentUser.getEmail());

        db.collection("users")
            .document(currentUser.getUid())
            .set(profile, SetOptions.merge())
                .addOnSuccessListener(aVoid -> Toast.makeText(
                        ProfileActivity.this,
                        R.string.profile_update_success,
                        Toast.LENGTH_SHORT
                ).show())
                .addOnFailureListener(e -> Toast.makeText(
                        ProfileActivity.this,
                        R.string.profile_update_failure,
                        Toast.LENGTH_SHORT
                ).show());
    }

    private void redirectToLogin() {
        Intent intent = new Intent(ProfileActivity.this, LoginActivity.class);
        startActivity(intent);
        finishAffinity();
    }
}
