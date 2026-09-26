package com.ahuguet.castellsenvena.core.data.groups

import com.ahuguet.castellsenvena.core.domain.groups.CastellerGroupDirectory
import com.ahuguet.castellsenvena.core.domain.groups.GroupDirectoryRepository
import com.ahuguet.castellsenvena.core.network.service.GroupDirectoryRemoteService

/** The Agenda filter keeps the last directory it saw, so no cache is needed here. */
class RemoteGroupDirectoryRepository(
    private val remoteService: GroupDirectoryRemoteService,
) : GroupDirectoryRepository {
    override suspend fun groupDirectory(forceRefresh: Boolean): CastellerGroupDirectory =
        remoteService.groupDirectory(forceRefresh)
}
