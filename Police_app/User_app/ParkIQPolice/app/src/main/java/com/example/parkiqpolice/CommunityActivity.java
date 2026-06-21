package com.example.parkiqpolice;

import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.MenuItem;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.PopupMenu;

import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

public class CommunityActivity extends BaseNavigationActivity {

    private static final int SORT_NEWEST = 0;
    private static final int SORT_HIGHEST_SCORE = 1;
    private static final int SORT_LOCATION = 2;
    private static final int SORT_STATUS = 3;

    // --- Class-level fields ---
    RecyclerView communityRecycler;
    EditText edtSearchCommunity;
    ImageButton btnSortCommunity;
    List<CommunityModel> allReports;
    List<CommunityModel> reportList;
    CommunityAdapter adapter;
    LoadingDialog loadingDialog;
    String currentSearchQuery = "";
    int currentSortOrder = SORT_NEWEST;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Initialise UI controls
        communityRecycler = findViewById(R.id.communityRecycler);
        edtSearchCommunity = findViewById(R.id.edtSearchCommunity);
        btnSortCommunity = findViewById(R.id.btnSortCommunity);

        communityRecycler.setLayoutManager(
                new LinearLayoutManager(this)
        );

        // Prepare data and adapter
        allReports = new ArrayList<>();
        reportList = new ArrayList<>();

        adapter = new CommunityAdapter(reportList);
        communityRecycler.setAdapter(adapter);

        // Load data from Firestore
        loadingDialog = new LoadingDialog(this);
        setupSearchAndSort();
        loadCommunityReports();
    }

    @Override
    protected int getContentLayoutId() {
        return R.layout.activity_community;
    }

    @Override
    protected int getSelectedMenuItemId() {
        return R.id.nav_community;
    }

    // --- Load data from "violations" collection ---
    private void loadCommunityReports() {
        loadingDialog.show();

        FriendFirebase
            .getFirestore(this)
            .collection("violations")
            .orderBy("timestamp", com.google.firebase.firestore.Query.Direction.DESCENDING)
            .get()
            .addOnSuccessListener(queryDocumentSnapshots -> {

                    allReports.clear();
                    reportList.clear();

                    for (var doc : queryDocumentSnapshots) {
                        CommunityModel report = doc.toObject(CommunityModel.class);
                        // if Firestore used Timestamp type, try mapping manually
                        if (report.getTimestamp() == 0) {
                            Object tsObj = doc.get("timestamp");
                            if (tsObj instanceof com.google.firebase.Timestamp) {
                                report = mapTimestamp(report, (com.google.firebase.Timestamp) tsObj);
                            } else if (tsObj instanceof Number) {
                                // already epoch millis
                                long v = ((Number) tsObj).longValue();
                                trySetTimestamp(report, v);
                            }
                        }

                        allReports.add(report);
                    }

                    applyFilters();
                    loadingDialog.hide();

                })
                .addOnFailureListener(e -> {
                    loadingDialog.hide();
                    // Optional: handle error (e.g., show a toast)
                });
    }

    private void setupSearchAndSort() {
        // compact sort popup from small button
        btnSortCommunity.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                PopupMenu popup = new PopupMenu(CommunityActivity.this, v);
                String[] options = getResources().getStringArray(R.array.community_sort_options);
                for (int i = 0; i < options.length; i++) {
                    popup.getMenu().add(0, i, i, options[i]);
                }
                popup.setOnMenuItemClickListener(new PopupMenu.OnMenuItemClickListener() {
                    @Override
                    public boolean onMenuItemClick(MenuItem item) {
                        currentSortOrder = item.getItemId();
                        applyFilters();
                        return true;
                    }
                });
                popup.show();
            }
        });

        edtSearchCommunity.addTextChangedListener(
                new TextWatcher() {
                    @Override
                    public void beforeTextChanged(CharSequence s,
                                                  int start,
                                                  int count,
                                                  int after) {
                    }

                    @Override
                    public void onTextChanged(CharSequence s,
                                              int start,
                                              int before,
                                              int count) {
                        currentSearchQuery = s.toString();
                        applyFilters();
                    }

                    @Override
                    public void afterTextChanged(Editable s) {
                    }
                }
        );
    }

        // small helpers to set timestamp on model when Firestore returns a Timestamp object
        private CommunityModel mapTimestamp(CommunityModel model, com.google.firebase.Timestamp ts) {
            trySetTimestamp(model, ts.toDate().getTime());
            return model;
        }

        private void trySetTimestamp(CommunityModel model, long millis) {
            try {
                java.lang.reflect.Field f = CommunityModel.class.getDeclaredField("timestamp");
                f.setAccessible(true);
                f.setLong(model, millis);
            } catch (Exception ignored) {
            }
        }

    private void applyFilters() {
        reportList.clear();

        String query = currentSearchQuery.trim().toLowerCase();
        for (CommunityModel report : allReports) {
            if (query.isEmpty()
                    || report.getLocation().toLowerCase().contains(query)
                    || report.getType().toLowerCase().contains(query)) {
                reportList.add(report);
            }
        }

        switch (currentSortOrder) {
            case SORT_HIGHEST_SCORE:
                Collections.sort(reportList,
                        Comparator.comparingLong(
                                CommunityModel::getScoreAwarded
                        ).reversed());
                break;
            case SORT_LOCATION:
                Collections.sort(reportList,
                        Comparator.comparing(
                                CommunityModel::getLocation,
                                String.CASE_INSENSITIVE_ORDER
                        ));
                break;
            case SORT_STATUS:
                Collections.sort(reportList,
                        Comparator.comparing(
                                CommunityModel::getStatus,
                                String.CASE_INSENSITIVE_ORDER
                        ));
                break;
            case SORT_NEWEST:
            default:
                // Keep original ordering from Firestore
                break;
        }

        adapter.notifyDataSetChanged();
    }
}