# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CustomSmartLink'
        db.create_table('smartlinks_customsmartlink', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('shortcuts', self.gf('django.db.models.fields.TextField')(max_length=300)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=1000, blank=True)),
        ))
        db.send_create_signal('smartlinks', ['CustomSmartLink'])


    def backwards(self, orm):
        # Deleting model 'CustomSmartLink'
        db.delete_table('smartlinks_customsmartlink')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'smartlinks.customsmartlink': {
            'Meta': {'object_name': 'CustomSmartLink'},
            'description': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shortcuts': ('django.db.models.fields.TextField', [], {'max_length': '300'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'smartlinks.indexentry': {
            'Meta': {'unique_together': "(('value', 'content_type', 'object_id'),)", 'object_name': 'IndexEntry'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '300', 'db_index': 'True'})
        }
    }

    complete_apps = ['smartlinks']