package com.sas.management.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.sas.management.ui.screens.auth.LoginScreen
import com.sas.management.ui.screens.dashboard.DashboardScreen
import com.sas.management.ui.screens.SplashScreen
import com.sas.management.ui.screens.modules.ModulesScreen
import com.sas.management.ui.screens.modules.ModuleDetailScreen

@Composable
fun SASNavigation() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = "splash"
    ) {
        composable("splash") {
            SplashScreen(
                onNavigateToLogin = { navController.navigate("login") },
                onNavigateToDashboard = { navController.navigate("dashboard") }
            )
        }
        
        composable("login") {
            LoginScreen(
                onLoginSuccess = { navController.navigate("dashboard") { popUpTo("splash") } },
                onNavigateBack = { navController.popBackStack() }
            )
        }
        
        composable("dashboard") {
            DashboardScreen(
                onNavigateToLogin = { 
                    navController.navigate("login") { 
                        popUpTo("dashboard") { inclusive = true }
                    }
                },
                onNavigateToModules = { navController.navigate("modules") }
            )
        }
        
        composable("modules") {
            ModulesScreen(
                onNavigateBack = { navController.popBackStack() },
                onModuleClick = { moduleId ->
                    navController.navigate("module/$moduleId")
                }
            )
        }
        
        composable("module/{moduleId}") { backStackEntry ->
            val moduleId = backStackEntry.arguments?.getString("moduleId") ?: ""
            ModuleDetailScreen(
                moduleId = moduleId,
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}

