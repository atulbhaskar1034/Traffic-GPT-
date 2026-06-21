package com.example.parkiqpolice;

import android.content.Intent;
import androidx.core.content.ContextCompat;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.google.android.material.bottomnavigation.BottomNavigationView;

public abstract class BaseNavigationActivity extends AppCompatActivity {

    protected abstract int getContentLayoutId();

    protected abstract int getSelectedMenuItemId();

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Use theme default status bar color and icon contrast
        getWindow().setStatusBarColor(ContextCompat.getColor(this, R.color.background));
        View decorView = getWindow().getDecorView();
        decorView.setSystemUiVisibility(decorView.getSystemUiVisibility() | View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);

        setContentView(getContentLayoutId());
        setupBottomNavigation();
    }

    private void setupBottomNavigation() {
        BottomNavigationView bottomNav = findViewById(R.id.bottomNavigation);
        if (bottomNav == null) {
            return;
        }

        bottomNav.setSelectedItemId(getSelectedMenuItemId());

        bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == getSelectedMenuItemId()) {
                return true;
            }

            Intent intent = null;
            if (id == R.id.nav_dashboard) {
                intent = new Intent(this, DashboardActivity.class);
            } else if (id == R.id.nav_hotspots) {
                intent = new Intent(this, HotspotsActivity.class);
            } else if (id == R.id.nav_community) {
                intent = new Intent(this, CommunityActivity.class);
            } else if (id == R.id.nav_profile) {
                intent = new Intent(this, ProfileActivity.class);
            }

            if (intent != null) {
                startActivityWithNoAnimation(intent);
                finish();
                overridePendingTransition(0, 0);
                return true;
            }
            return false;
        });
    }

    protected void startActivityWithNoAnimation(Intent intent) {
        startActivity(intent);
        overridePendingTransition(0, 0);
    }
}
