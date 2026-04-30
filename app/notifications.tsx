import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Colors } from "../constants/colors";
import { useAuth } from "../context/AuthContext";
import { NotificationItem, notificationService } from "../services/notificationService";

// Helper function to format date nicely
const formatTimeAgo = (dateStr: string) => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 60) return `${diffMins || 1} phút trước`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} giờ trước`;
  
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return `Hôm qua lúc ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
  if (diffDays < 7) return `${diffDays} ngày trước`;
  
  return `${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')}/${date.getFullYear()}`;
};

export default function NotificationsScreen() {
  const insets = useSafeAreaInsets();
  const { token } = useAuth();
  
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const fetchNotis = async () => {
    try {
      const res = await notificationService.getNotifications(50, 0, false);
      setNotifications(res.items || []);
      setUnreadCount(res.unread_count || 0);
    } catch (e) {
      console.log("Failed to fetch notifications", e);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNotis();
  }, [token]);

  const onRefresh = useCallback(() => {
    setIsRefreshing(true);
    fetchNotis();
  }, [token]);

  const handleMarkAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (e) {
      console.log("Mark all read failed");
    }
  };

  const handleNotificationPress = async (item: NotificationItem) => {
    // Nếu chưa đọc thì mark as read ngay lập tức trên UI và gọi API
    if (!item.is_read) {
      setNotifications(prev => 
        prev.map(n => n.notification_id === item.notification_id ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
      notificationService.markAsRead(item.notification_id).catch(() => {});
    }

    // Xử lý action URL
    if (item.action_url) {
      // API hiện tại trả về action_url dạng: "/analysis-result/uuid..."
      // Yêu cầu là đẩy thẳng vào history-detail
      const parts = item.action_url.split("/");
      const id = parts[parts.length - 1];
      if (id) {
        router.push({ pathname: '/history-detail' as any, params: { analysisId: id } });
      }
    }
  };

  const renderItem = ({ item }: { item: NotificationItem }) => {
    const isUnread = !item.is_read;
    return (
      <TouchableOpacity
        style={[styles.notificationCard, isUnread && styles.notificationCardUnread]}
        activeOpacity={0.7}
        onPress={() => handleNotificationPress(item)}
      >
        <View style={styles.iconBox}>
           {/* Icon tuỳ vào notification_type. Trong TH này dùng chung icon lục giác/check */}
           {item.notification_type === 'analysis_complete' ? (
              <View style={[styles.iconWrapper, { backgroundColor: isUnread ? Colors.primary + '20' : Colors.backgroundSecondary }]}>
                 <Feather name="file-text" size={18} color={isUnread ? Colors.primary : Colors.textMuted} />
              </View>
           ) : (
              <View style={[styles.iconWrapper, { backgroundColor: isUnread ? Colors.primary + '20' : Colors.backgroundSecondary }]}>
                 <Feather name="bell" size={18} color={isUnread ? Colors.primary : Colors.textMuted} />
              </View>
           )}
        </View>
        
        <View style={styles.contentBox}>
           <Text style={[styles.title, isUnread && styles.titleUnread]} numberOfLines={2}>
             {item.title}
           </Text>
           <Text style={styles.body} numberOfLines={3}>
             {item.body}
           </Text>
           <Text style={styles.time}>{formatTimeAgo(item.created_at)}</Text>
        </View>
        
        {isUnread && <View style={styles.unreadIndicator} />}
      </TouchableOpacity>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.background} />
      
      {/* ── Top Bar ── */}
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Feather name="arrow-left" size={24} color={Colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.topBarTitle}>
          Thông báo {unreadCount > 0 && `(${unreadCount > 99 ? '99+' : unreadCount})`}
        </Text>
        <TouchableOpacity style={styles.markAllBtn} onPress={handleMarkAllAsRead}>
          <Feather name="check-square" size={20} color={Colors.primary} />
        </TouchableOpacity>
      </View>

      {/* ── Content ── */}
      {isLoading ? (
        <View style={styles.centerBox}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : notifications.length === 0 ? (
        <View style={styles.centerBox}>
          <Feather name="bell-off" size={48} color={Colors.borderLight} />
          <Text style={styles.emptyText}>Bạn không có thông báo nào</Text>
        </View>
      ) : (
        <FlatList
          data={notifications}
          keyExtractor={item => item.notification_id}
          renderItem={renderItem}
          contentContainerStyle={[styles.listContent, { paddingBottom: insets.bottom + 20 }]}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={onRefresh}
              colors={[Colors.primary]}
            />
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary, // Nền xám nhạt để thẻ trắng nổi bật
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: Colors.background,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  backBtn: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'flex-start',
  },
  topBarTitle: {
    fontSize: 18,
    fontFamily: 'Inter_700Bold',
    color: Colors.textPrimary,
  },
  markAllBtn: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'flex-end',
  },
  centerBox: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    gap: 12,
  },
  emptyText: {
    fontSize: 15,
    fontFamily: 'Inter_500Medium',
    color: Colors.textMuted,
  },
  
  // Danh sách thẻ
  listContent: {
    padding: 16,
    gap: 12,
  },
  notificationCard: {
    flexDirection: 'row',
    backgroundColor: Colors.background,
    borderRadius: 16,
    padding: 16,
    gap: 14,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    // Xóa viền xám theo yêu cầu User
    borderWidth: 0,
  },
  notificationCardUnread: {
    backgroundColor: Colors.backgroundChat, // Đổi sang Solid Color để xoá hoàn toàn lỗi tràn xám (bleed effect) ở Android
  },
  iconBox: {
    paddingTop: 2,
  },
  iconWrapper: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  contentBox: {
    flex: 1,
    gap: 4,
  },
  title: {
    fontSize: 15,
    fontFamily: 'Inter_600SemiBold',
    color: Colors.textPrimary,
    lineHeight: 20,
  },
  titleUnread: {
    color: Colors.primary,
  },
  body: {
    fontSize: 13,
    fontFamily: 'Inter_400Regular',
    color: Colors.textLight,
    lineHeight: 18,
  },
  time: {
    fontSize: 12,
    fontFamily: 'Inter_500Medium',
    color: Colors.textMuted,
    marginTop: 4,
  },
  unreadIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.primary,
    position: 'absolute',
    top: 18,
    right: 16,
  }
});
