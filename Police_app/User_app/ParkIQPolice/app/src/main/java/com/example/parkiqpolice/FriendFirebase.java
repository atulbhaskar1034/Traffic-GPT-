package com.example.parkiqpolice;

import android.content.Context;

import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.firestore.FirebaseFirestore;

public class FriendFirebase {

    private static FirebaseFirestore firestore;

    public static FirebaseFirestore getFirestore(
            Context context
    ) {

        if (firestore != null) {
            return firestore;
        }

        FirebaseOptions options =
                new FirebaseOptions.Builder()
                        .setProjectId("trafic-gpt")
                        .setApplicationId(
                                "1:383562546234:android:1fb438aa0e471b50f8c903"
                        )
                        .setApiKey(
                                "AIzaSyCirx-rqBUyaz0nv57shmgZp43a7ANCrb4"
                        )
                        .build();

        FirebaseApp friendApp;

        try {

            friendApp =
                    FirebaseApp.initializeApp(
                            context,
                            options,
                            "FriendApp"
                    );

        } catch (Exception e) {

            friendApp =
                    FirebaseApp.getInstance(
                            "FriendApp"
                    );
        }

        firestore =
                FirebaseFirestore.getInstance(
                        friendApp
                );

        return firestore;
    }
}