package com.sas.management.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sas.management.data.api.ApiClient
import com.sas.management.data.model.DashboardSummary
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class DashboardViewModel : ViewModel() {
    private val apiService = ApiClient.apiService

    private val _dashboardState = MutableStateFlow<DashboardState>(DashboardState.Loading)
    val dashboardState: StateFlow<DashboardState> = _dashboardState

    fun loadDashboard() {
        viewModelScope.launch {
            _dashboardState.value = DashboardState.Loading
            try {
                val response = apiService.getDashboardSummary()
                if (response.isSuccessful && response.body() != null) {
                    _dashboardState.value = DashboardState.Success(response.body()!!)
                } else {
                    _dashboardState.value = DashboardState.Error(
                        "Failed to load dashboard"
                    )
                }
            } catch (e: Exception) {
                _dashboardState.value = DashboardState.Error(
                    e.message ?: "Network error"
                )
            }
        }
    }

    sealed class DashboardState {
        object Loading : DashboardState()
        data class Success(val summary: DashboardSummary) : DashboardState()
        data class Error(val message: String) : DashboardState()
    }
}

