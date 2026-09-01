#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OCR支持的所有语言
"""

import requests
import json
import time
from typing import Dict, List

class OCRLanguageTester:
    """OCR语言测试器"""
    
    def __init__(self, api_base_url: str = "http://localhost:16110", api_key: str = None):
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
    
    def test_language_support(self, language: str) -> Dict:
        """测试单个语言支持"""
        print(f"测试语言: {language}")
        
        # 创建测试文本
        test_text = f"{language.upper()} Text Recognition"
        
        # 创建简单的测试图片（使用PIL）
        from PIL import Image, ImageDraw, ImageFont
        import os
        
        # 创建测试图片
        img = Image.new('RGB', (400, 100), 'white')
        draw = ImageDraw.Draw(img)
        
        # 使用默认字体
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 30), test_text, fill='black', font=font)
        
        # 保存临时图片
        temp_image = f"temp_test_{language}.jpg"
        img.save(temp_image)
        
        try:
            # 发送OCR请求
            with open(temp_image, 'rb') as f:
                files = {'file': (temp_image, f, 'image/jpeg')}
                data = {'language': language}
                
                response = self.session.post(
                    f"{self.api_base_url}/v1/ocr",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            # 清理临时文件
            os.remove(temp_image)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    recognized_texts = []
                    if result.get('data'):
                        for item in result['data']:
                            if 'text' in item:
                                recognized_texts.append(item['text'])
                    
                    return {
                        'success': True,
                        'language': language,
                        'recognized_texts': recognized_texts,
                        'expected_text': test_text,
                        'response': result
                    }
                else:
                    return {
                        'success': False,
                        'language': language,
                        'error': result.get('msg', 'Unknown error'),
                        'response': result
                    }
            else:
                return {
                    'success': False,
                    'language': language,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'response': None
                }
                
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_image):
                os.remove(temp_image)
            return {
                'success': False,
                'language': language,
                'error': str(e),
                'response': None
            }
    
    def test_all_supported_languages(self):
        """测试所有支持的语言"""
        # 从main.py中提取支持的语言
        supported_languages = [
            # 主要语言
            'zh', 'en', 'ja', 'ko', 'th', 'ru',
            # 拉丁语系
            'fr', 'de', 'es', 'it', 'pt', 'nl', 'pl', 'cs', 'sk', 'hu', 'ro', 'bg', 'hr', 'sl', 'et', 'lv', 'lt', 'el', 'he', 'is', 'ga', 'cy', 'mt', 'sq', 'mk', 'uk', 'be', 'kk', 'ky', 'uz', 'tg', 'mn', 'bo', 'dz', 'si', 'ta', 'te', 'kn', 'ml', 'gu', 'pa', 'or', 'as', 'bn', 'ur', 'ne', 'mr', 'sa', 'sd', 'ps', 'fa', 'ku', 'my', 'km', 'lo', 'am', 'ti', 'om', 'so', 'sw', 'yo', 'ig', 'ha', 'zu', 'xh', 'af', 'st', 'tn', 'ss', 've', 'ts', 'nr', 'nso', 'tk', 'az', 'ab', 'ru_mold', 'oc', 'rs_cyrillic', 'rs_latin', 'sr', 'latin', 'eslav'
        ]
        
        print("开始测试OCR支持的所有语言...")
        print("=" * 60)
        
        results = []
        success_count = 0
        
        for lang in supported_languages:
            try:
                result = self.test_language_support(lang)
                results.append(result)
                
                if result['success']:
                    success_count += 1
                    print(f"✅ {lang}: 支持 - {result['recognized_texts']}")
                else:
                    print(f"❌ {lang}: 不支持 - {result['error']}")
                    
            except Exception as e:
                print(f"❌ {lang}: 测试异常 - {str(e)}")
                results.append({
                    'success': False,
                    'language': lang,
                    'error': str(e),
                    'response': None
                })
            
            time.sleep(0.5)  # 避免请求过于频繁
        
        print("=" * 60)
        print(f"测试完成!")
        print(f"总语言数: {len(supported_languages)}")
        print(f"支持语言数: {success_count}")
        print(f"支持率: {success_count/len(supported_languages)*100:.1f}%")
        
        # 保存结果
        with open('language_support_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: language_support_results.json")
        
        return results

def main():
    """主函数"""
    tester = OCRLanguageTester(
        api_base_url="http://localhost:16110",
        api_key=os.environ.get("POLYOCR_API_KEY", "")
    )
    
    results = tester.test_all_supported_languages()
    
    # 显示支持的语言列表
    supported_langs = [r['language'] for r in results if r['success']]
    print(f"\n支持的语言: {', '.join(supported_langs)}")

if __name__ == "__main__":
    main()


