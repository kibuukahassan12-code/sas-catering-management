package com.sas.management.data.api

import com.sas.management.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    // Authentication
    @POST("/login")
    @FormUrlEncoded
    suspend fun login(
        @Field("email") email: String,
        @Field("password") password: String,
        @Field("remember_me") rememberMe: Boolean = false
    ): Response<LoginResponse>

    @POST("/logout")
    suspend fun logout(): Response<Unit>

    // Dashboard
    @GET("/api/dashboard/summary")
    suspend fun getDashboardSummary(): Response<DashboardSummary>

    // Events
    @GET("/api/events")
    suspend fun getEvents(): Response<List<Event>>

    @GET("/api/events/{id}")
    suspend fun getEvent(@Path("id") id: Int): Response<Event>

    // Search
    @GET("/search/api/quick")
    suspend fun quickSearch(@Query("q") query: String): Response<SearchResponse>

    // User
    @GET("/api/user/profile")
    suspend fun getUserProfile(): Response<UserProfile>
}

