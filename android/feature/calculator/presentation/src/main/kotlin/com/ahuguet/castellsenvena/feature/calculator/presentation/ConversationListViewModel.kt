package com.ahuguet.castellsenvena.feature.calculator.presentation

import com.ahuguet.castellsenvena.core.common.runCatchingCancellable
import com.ahuguet.castellsenvena.core.common.userMessage
import com.ahuguet.castellsenvena.core.domain.chat.ChatConversationSummary
import com.ahuguet.castellsenvena.core.domain.chat.ChatRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class ConversationListState(
    /** Most recently updated first. */
    val conversations: List<ChatConversationSummary> = emptyList(),
    val errorMessage: String? = null,
)

class ConversationListViewModel(private val repository: ChatRepository) {
    private val mutableState = MutableStateFlow(ConversationListState())
    val state: StateFlow<ConversationListState> = mutableState.asStateFlow()

    suspend fun reload() {
        runCatchingCancellable { repository.listConversations() }
            .onSuccess { mutableState.value = ConversationListState(conversations = it) }
            .onFailure(::showError)
    }

    suspend fun delete(id: String) {
        runCatchingCancellable { repository.deleteConversation(id) }
            .onSuccess { reload() }
            .onFailure(::showError)
    }

    suspend fun rename(id: String, title: String) {
        runCatchingCancellable { repository.renameConversation(id, title) }
            .onSuccess { reload() }
            .onFailure(::showError)
    }

    private fun showError(failure: Throwable) {
        mutableState.value = mutableState.value.copy(errorMessage = failure.userMessage())
    }
}
