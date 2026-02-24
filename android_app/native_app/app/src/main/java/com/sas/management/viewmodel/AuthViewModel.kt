package com.sas.management.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sas.management.data.api.ApiClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class AuthViewModel : ViewModel() {
    private val apiService = ApiClient.apiService

    private val _loginState = MutableStateFlow<LoginState>(LoginState.Idle)
    val loginState: StateFlow<LoginState> = _loginState

    fun login(email: String, password: String) {
        viewModelScope.launch {
            _loginState.value = LoginState.Loading
            try {
                val response = apiService.login(email, password, false)
                if (response.isSuccessful) {
                    val body = response.body()
                    // Flask returns redirect or success, check response code
                    if (response.code() == 200 || response.code() == 302 || (body != null && body.success)) {
                        _loginState.value = LoginState.Success
                    } else {
                        // Try to parse error from response
                        val errorMsg = body?.message ?: "Invalid credentials"
                        _loginState.value = LoginState.Error(errorMsg)
                    }
                } else {
                    // Handle different error codes
                    val errorMsg = when (response.code()) {
                        401 -> "Invalid email or password"
                        429 -> "Too many login attempts. Please try again later"
                        500 -> "Server error. Please try again"
                        else -> "Login failed. Please check your connection"
                    }
                    _loginState.value = LoginState.Error(errorMsg)
                }
            } catch (e: java.net.UnknownHostException) {
                _loginState.value = LoginState.Error("Cannot connect to server. Please check your network and backend URL")
            } catch (e: java.net.ConnectException) {
                _loginState.value = LoginState.Error("Cannot connect to server. Please ensure the backend is running")
            } catch (e: Exception) {
                _loginState.value = LoginState.Error(e.message ?: "Network error occurred")
            }
        }
    }

    sealed class LoginState {
        object Idle : LoginState()
        object Loading : LoginState()
        object Success : LoginState()
        data class Error(val message: String) : LoginState()
    }
}

