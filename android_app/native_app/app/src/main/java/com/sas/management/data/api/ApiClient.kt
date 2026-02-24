package com.sas.management.data.api

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {
    // Change this to your Flask backend URL
    private const val BASE_URL = "http://10.0.2.2:10000" // Android emulator
    // For physical device: "http://YOUR_LOCAL_IP:10000"
    // For production: "https://your-domain.com"

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val cookieJar = object : okhttp3.CookieJar {
        private val cookies = mutableListOf<okhttp3.Cookie>()
        
        override fun saveFromResponse(url: okhttp3.HttpUrl, cookies: List<okhttp3.Cookie>) {
            this.cookies.clear()
            this.cookies.addAll(cookies)
        }
        
        override fun loadForRequest(url: okhttp3.HttpUrl): List<okhttp3.Cookie> {
            return cookies
        }
    }
    
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .cookieJar(cookieJar)
        .addInterceptor { chain ->
            val original = chain.request()
            val requestBuilder = original.newBuilder()
            
            // Set content type for form data
            if (original.body is okhttp3.FormBody) {
                requestBuilder.header("Content-Type", "application/x-www-form-urlencoded")
            } else {
                requestBuilder.header("Content-Type", "application/json")
            }
            
            // Add user agent
            requestBuilder.header("User-Agent", "SAS-Android-App/1.0")
            
            val request = requestBuilder.build()
            chain.proceed(request)
        }
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    val apiService: ApiService = retrofit.create(ApiService::class.java)
}

