package com.example.parkiqpolice;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.google.android.gms.auth.api.signin.GoogleSignIn;
import com.google.android.gms.auth.api.signin.GoogleSignInAccount;
import com.google.android.gms.auth.api.signin.GoogleSignInClient;
import com.google.android.gms.auth.api.signin.GoogleSignInOptions;
import com.google.android.gms.common.api.ApiException;
import com.google.firebase.auth.AuthCredential;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.GoogleAuthProvider;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.QuerySnapshot;

public class LoginActivity extends AppCompatActivity {

    private static final int RC_SIGN_IN = 100;

    private FirebaseAuth mAuth;
    private GoogleSignInClient googleSignInClient;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        mAuth = FirebaseAuth.getInstance();

        // Skip Login if already signed in
        if (mAuth.getCurrentUser() != null) {

            startActivity(
                    new Intent(
                            LoginActivity.this,
                            DashboardActivity.class
                    )
            );

            finish();
            return;
        }

        GoogleSignInOptions gso =
                new GoogleSignInOptions.Builder(
                        GoogleSignInOptions.DEFAULT_SIGN_IN)
                        .requestIdToken("54777348115-3hvukpm48fpiq7oef49b9pj17s92vl5b.apps.googleusercontent.com")
                        .requestEmail()
                        .build();

        googleSignInClient = GoogleSignIn.getClient(this, gso);

        Button googleBtn = findViewById(R.id.googleSignInBtn);

        googleBtn.setOnClickListener(v -> {

            // Force Account Picker
            googleSignInClient.signOut()
                    .addOnCompleteListener(task -> {

                        Intent signInIntent =
                                googleSignInClient.getSignInIntent();

                        startActivityForResult(
                                signInIntent,
                                RC_SIGN_IN
                        );

                    });

        });
    }

    @Override
    protected void onActivityResult(
            int requestCode,
            int resultCode,
            @Nullable Intent data) {

        super.onActivityResult(
                requestCode,
                resultCode,
                data
        );

        if (requestCode == RC_SIGN_IN) {

            try {

                GoogleSignInAccount account =
                        GoogleSignIn.getSignedInAccountFromIntent(data)
                                .getResult(ApiException.class);

                firebaseAuth(account.getIdToken());

            } catch (Exception e) {

                Toast.makeText(
                        this,
                        e.getMessage(),
                        Toast.LENGTH_LONG
                ).show();
            }
        }
    }

    private void firebaseAuth(String idToken) {

        AuthCredential credential =
                GoogleAuthProvider.getCredential(
                        idToken,
                        null
                );

        mAuth.signInWithCredential(credential)
                .addOnCompleteListener(this, task -> {

                    if (task.isSuccessful()) {

                        String email =
                                FirebaseAuth.getInstance()
                                        .getCurrentUser()
                                        .getEmail();

                        FirebaseFirestore db = FirebaseFirestore.getInstance();

                        // Prefer unified `users` collection with a `role` field.
                        db.collection("users")
                                .whereEqualTo("email", email)
                                .whereEqualTo("role", "police")
                                .get()
                                .addOnCompleteListener(usersTask -> {

                                    boolean found = usersTask.isSuccessful()
                                            && !usersTask.getResult().isEmpty();

                                    if (found) {
                                        // Police user exists in unified collection
                                        Toast.makeText(
                                                LoginActivity.this,
                                                "Police Login Successful",
                                                Toast.LENGTH_SHORT
                                        ).show();

                                        startActivity(
                                                new Intent(
                                                        LoginActivity.this,
                                                        DashboardActivity.class
                                                )
                                        );

                                        finish();
                                        return;
                                    }

                                    // Fallback: check legacy `police_users` collection and migrate
                                    db.collection("police_users")
                                            .whereEqualTo("email", email)
                                            .get()
                                            .addOnCompleteListener(oldTask -> {

                                                if (oldTask.isSuccessful()
                                                        && !oldTask.getResult().isEmpty()) {

                                                    var doc = oldTask.getResult().getDocuments().get(0);
                                                    var data = doc.getData();

                                                    if (data == null) data = new java.util.HashMap<>();
                                                    data.put("role", "police");

                                                    // Save migrated profile under unified `users` using auth UID
                                                    String uid = FirebaseAuth.getInstance().getCurrentUser().getUid();
                                                    db.collection("users")
                                                            .document(uid)
                                                            .set(data)
                                                            .addOnSuccessListener(aVoid -> {
                                                                // Optionally, remove the legacy document
                                                                doc.getReference().delete();

                                                                Toast.makeText(
                                                                        LoginActivity.this,
                                                                        "Police Login Successful",
                                                                        Toast.LENGTH_SHORT
                                                                ).show();

                                                                startActivity(
                                                                        new Intent(
                                                                                LoginActivity.this,
                                                                                DashboardActivity.class
                                                                        )
                                                                );

                                                                finish();
                                                            })
                                                            .addOnFailureListener(e -> {
                                                                FirebaseAuth.getInstance().signOut();
                                                                Toast.makeText(
                                                                        LoginActivity.this,
                                                                        "Access Denied. Migration failed.",
                                                                        Toast.LENGTH_LONG
                                                                ).show();
                                                            });

                                                } else {
                                                    FirebaseAuth.getInstance().signOut();

                                                    Toast.makeText(
                                                            LoginActivity.this,
                                                            "Access Denied. Not a registered officer.",
                                                            Toast.LENGTH_LONG
                                                    ).show();
                                                }
                                            });
                                });

                    } else {

                        Toast.makeText(
                                this,
                                "Login Failed",
                                Toast.LENGTH_SHORT
                        ).show();
                    }
                });
    }
}