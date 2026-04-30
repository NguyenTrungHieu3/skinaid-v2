// app/knowledge-detail.tsx

import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router, useLocalSearchParams } from 'expo-router';
import React, { useCallback, useEffect, useRef } from 'react';
import {
  Animated,
  Easing,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  KNOWLEDGE_ARTICLES,
  KnowledgeSection,
} from '../constants/knowledgeArticles';

// Inter fonts (Inter_400Regular, Inter_500Medium, Inter_600SemiBold) are loaded
// globally in app/_layout.tsx — reference them via fontFamily strings only.

// ─── Section Item (animated wrapper lives in parent) ─────────────────────────
type SectionItemProps = {
  section: KnowledgeSection;
  isLast: boolean;
  opacity: Animated.Value;
  translateY: Animated.Value;
};

function SectionItem({ section, isLast, opacity, translateY }: SectionItemProps) {
  return (
    <Animated.View
      style={[
        styles.sectionAnimWrapper,
        { opacity, transform: [{ translateY }] },
      ]}
    >
      <View style={styles.sectionRow}>
        {/* Icon box */}
        <View style={[styles.iconBox, { backgroundColor: section.iconBg }]}>
          <Text style={styles.iconEmoji}>{section.icon}</Text>
        </View>

        {/* Text group */}
        <View style={styles.sectionTextGroup}>
          <Text style={styles.sectionTitle}>{section.title}</Text>
          <Text style={styles.sectionBody}>{section.text}</Text>
        </View>
      </View>

      {/* Separator (skip on last item) */}
      {!isLast && <View style={styles.sectionSeparator} />}
    </Animated.View>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────
export default function KnowledgeDetailScreen() {
  const insets = useSafeAreaInsets();
  const { articleId } = useLocalSearchParams<{ articleId: string }>();

  const article = KNOWLEDGE_ARTICLES.find((a) => a.id === articleId);

  // ── Hero floating animation ────────────────────────────────────────────────
  const floatAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, {
          toValue: -10,
          duration: 1100,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim, {
          toValue: 0,
          duration: 1100,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [floatAnim]);

  // ── Section entry animations (staggered) ──────────────────────────────────
  const sectionsCount = article?.sections.length ?? 0;

  // Lazily init anim values so count always matches sections
  const itemAnimsRef = useRef<{ opacity: Animated.Value; translateY: Animated.Value }[]>([]);
  if (itemAnimsRef.current.length !== sectionsCount) {
    itemAnimsRef.current = Array.from({ length: sectionsCount }, () => ({
      opacity: new Animated.Value(0),
      translateY: new Animated.Value(18),
    }));
  }

  useEffect(() => {
    if (sectionsCount === 0) return;

    const animations = itemAnimsRef.current.map((anim, index) =>
      Animated.parallel([
        Animated.timing(anim.opacity, {
          toValue: 1,
          duration: 350,
          delay: index * 55,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.timing(anim.translateY, {
          toValue: 0,
          duration: 350,
          delay: index * 55,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
      ])
    );

    Animated.parallel(animations).start();
  }, [sectionsCount]);

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleBack = useCallback(() => {
    router.back();
  }, []);

  // ── Null fallback ─────────────────────────────────────────────────────────
  if (!article) {
    return (
      <View style={styles.fallbackRoot}>
        <StatusBar barStyle="dark-content" translucent backgroundColor="transparent" />
        <TouchableOpacity
          style={[styles.backBtn, { top: insets.top + 8 }]}
          onPress={handleBack}
          activeOpacity={0.8}
        >
          <Ionicons name="chevron-back" size={22} color="#1A1A1A" />
        </TouchableOpacity>
        <Text style={styles.fallbackText}>Không tìm thấy nội dung</Text>
      </View>
    );
  }

  return (
    <View style={styles.root}>
      <StatusBar barStyle="dark-content" translucent backgroundColor="transparent" />

      {/* ── Floating Back Button (absolute, always on top) ─────────────── */}
      <TouchableOpacity
        style={[styles.backBtn, { top: insets.top + 8 }]}
        onPress={handleBack}
        activeOpacity={0.8}
      >
        <Ionicons name="chevron-back" size={22} color="#1A1A1A" />
      </TouchableOpacity>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingBottom: insets.bottom + 32 },
        ]}
        showsVerticalScrollIndicator={false}
        bounces
      >
        {/* ── Hero Section ──────────────────────────────────────────── */}
        <View style={[styles.hero, { backgroundColor: article.heroBg }]}>
          {/* Floating emoji */}
          <Animated.Text
            style={[styles.heroEmoji, { transform: [{ translateY: floatAnim }] }]}
          >
            {article.heroEmoji}
          </Animated.Text>

          {/* Tag badge (bottom-left) */}
          <View style={styles.heroBadgeContainer}>
            <View style={[styles.heroBadge, { backgroundColor: article.tagColor }]}>
              <Text style={styles.heroBadgeText}>{article.tag}</Text>
            </View>
          </View>

          {/* Gradient overlay: blend hero into white content below */}
          <LinearGradient
            colors={['transparent', '#FFFFFF']}
            style={styles.heroGradient}
            pointerEvents="none"
          />
        </View>

        {/* ── Content ──────────────────────────────────────────────── */}
        <View style={styles.content}>
          {/* Title */}
          <Text style={styles.articleTitle}>{article.title}</Text>

          {/* Divider */}
          <View style={styles.titleDivider} />

          {/* Section items */}
          {article.sections.map((section, index) => (
            <SectionItem
              key={`${article.id}-section-${index}`}
              section={section}
              isLast={index === article.sections.length - 1}
              opacity={itemAnimsRef.current[index].opacity}
              translateY={itemAnimsRef.current[index].translateY}
            />
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  // ── Root ──────────────────────────────────────────────────────────────────
  root: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  fallbackRoot: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  fallbackText: {
    fontSize: 15,
    fontFamily: 'Inter_400Regular',
    color: '#9CA3AF',
  },

  // ── Scroll ────────────────────────────────────────────────────────────────
  scroll: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },

  // ── Floating Back Button ──────────────────────────────────────────────────
  backBtn: {
    position: 'absolute',
    left: 16,
    zIndex: 100,
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(255,255,255,0.85)',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
    elevation: 4,
  },

  // ── Hero ──────────────────────────────────────────────────────────────────
  hero: {
    height: 240,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    position: 'relative',
  },
  heroEmoji: {
    fontSize: 90,
    lineHeight: 110,
    textAlign: 'center',
  },
  heroBadgeContainer: {
    position: 'absolute',
    bottom: 16,
    left: 16,
  },
  heroBadge: {
    borderRadius: 20,
    paddingVertical: 5,
    paddingHorizontal: 12,
  },
  heroBadgeText: {
    fontSize: 11,
    fontFamily: 'Inter_600SemiBold',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  heroGradient: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 80,
  },

  // ── Content ───────────────────────────────────────────────────────────────
  content: {
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  articleTitle: {
    fontSize: 22,
    fontFamily: 'Inter_600SemiBold',
    color: '#0D0D0D',
    lineHeight: 30,
    marginBottom: 20,
  },
  titleDivider: {
    height: 1,
    backgroundColor: '#F0F0F0',
    marginBottom: 20,
  },

  // ── Section Item ──────────────────────────────────────────────────────────
  sectionAnimWrapper: {
    // Wrapper receives opacity + translateY from Animated.Value
  },
  sectionRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 16,
  },
  iconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  iconEmoji: {
    fontSize: 20,
    lineHeight: 24,
  },
  sectionTextGroup: {
    flex: 1,
    paddingTop: 2,
  },
  sectionTitle: {
    fontSize: 14,
    fontFamily: 'Inter_500Medium',
    color: '#1A1A1A',
    marginBottom: 4,
    lineHeight: 20,
  },
  sectionBody: {
    fontSize: 13,
    fontFamily: 'Inter_400Regular',
    color: '#6B7280',
    lineHeight: 20,
  },
  sectionSeparator: {
    height: 1,
    backgroundColor: '#F5F5F5',
    marginBottom: 16,
  },
});
