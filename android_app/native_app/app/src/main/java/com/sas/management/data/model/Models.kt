package com.sas.management.data.model

import com.google.gson.annotations.SerializedName

// Authentication
data class LoginResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String?,
    @SerializedName("user") val user: User?
)

data class User(
    @SerializedName("id") val id: Int,
    @SerializedName("email") val email: String,
    @SerializedName("name") val name: String?,
    @SerializedName("role") val role: String?
)

// Dashboard
data class DashboardSummary(
    @SerializedName("upcoming_events_count") val upcomingEventsCount: Int,
    @SerializedName("pipeline_value") val pipelineValue: Double,
    @SerializedName("active_staff_count") val activeStaffCount: Int,
    @SerializedName("pending_tasks_count") val pendingTasksCount: Int
)

// Events
data class Event(
    @SerializedName("id") val id: Int,
    @SerializedName("name") val name: String,
    @SerializedName("date") val date: String,
    @SerializedName("venue") val venue: String?,
    @SerializedName("status") val status: String?
)

// Search
data class SearchResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("results") val results: List<SearchResult>?
)

data class SearchResult(
    @SerializedName("text") val text: String,
    @SerializedName("url") val url: String,
    @SerializedName("icon") val icon: String?,
    @SerializedName("subtext") val subtext: String?
)

// User Profile
data class UserProfile(
    @SerializedName("id") val id: Int,
    @SerializedName("email") val email: String,
    @SerializedName("name") val name: String?,
    @SerializedName("role") val role: String?
)

